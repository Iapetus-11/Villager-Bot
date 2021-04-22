import threading
import aiohttp
import asyncio
import logging
import struct
import time
import json
import zlib
import sys

from discord.gateway import WebSocketClosure, log, KeepAliveHandler, ReconnectWebSocket, EventListener
from discord.errors import InvalidArgument, ConnectionClosed
from discord.activity import BaseActivity
from discord import utils

cdef class GatewayRatelimiter:
    cdef public int max
    cdef public int remaining
    cdef public float window
    cdef public float per
    cdef public object lock
    cdef public object shard_id

    def __init__(self, count: int = 110, per: float = 60.0):
        # The default is 110 to give room for at least 10 heartbeats per minute
        self.max = count
        self.remaining = count
        self.window = 0.0
        self.per = per
        self.lock = asyncio.Lock()
        self.shard_id = None

    cpdef bint is_ratelimited(self):
        cdef float current = time.time()

        if current > self.window + self.per:
            return False

        return self.remaining == 0

    cpdef float get_delay(self):
        cdef float current = time.time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        if self.remaining == 0:
            self.window = current

        return 0.0

    async def block(self):
        async with self.lock:
            delta = self.get_delay()

            if delta:
                log.warning('WebSocket in shard ID %s is ratelimited, waiting %.2f seconds', self.shard_id, delta)
                await asyncio.sleep(delta)

cdef class DiscordWebSocket:
    """Implements a WebSocket for Discord's gateway v6.
    Attributes
    -----------
    DISPATCH
        Receive only. Denotes an event to be sent to Discord, such as READY.
    HEARTBEAT
        When received tells Discord to keep the connection alive.
        When sent asks if your connection is currently alive.
    IDENTIFY
        Send only. Starts a new session.
    PRESENCE
        Send only. Updates your presence.
    VOICE_STATE
        Send only. Starts a new connection to a voice guild.
    VOICE_PING
        Send only. Checks ping time to a voice guild, do not use.
    RESUME
        Send only. Resumes an existing connection.
    RECONNECT
        Receive only. Tells the client to reconnect to a new gateway.
    REQUEST_MEMBERS
        Send only. Asks for the full member list of a guild.
    INVALIDATE_SESSION
        Receive only. Tells the client to optionally invalidate the session
        and IDENTIFY again.
    HELLO
        Receive only. Tells the client the heartbeat interval.
    HEARTBEAT_ACK
        Receive only. Confirms receiving of a heartbeat. Not having it implies
        a connection issue.
    GUILD_SYNC
        Send only. Requests a guild sync.
    gateway
        The gateway we are currently connected to.
    token
        The authentication token for discord.
    """

    cdef object socket
    cdef object loop
    cdef list _dispatch_listeners
    cdef object _keep_alive
    cdef object thread_id
    cdef object session_id
    cdef object sequence
    cdef object _zlib
    cdef bytearray _buffer
    cdef object _close_code
    cdef GatewayRatelimiter _rate_limiter

    def __init__(self, socket, *, loop):
        self.socket = socket
        self.loop = loop

        # generic event listeners
        self._dispatch_listeners = []
        # the keep alive
        self._keep_alive = None
        self.thread_id = threading.get_ident()

        # ws related stuff
        self.session_id = None
        self.sequence = None
        self._zlib = zlib.decompressobj()
        self._buffer = bytearray()
        self._close_code = None
        self._rate_limiter = GatewayRatelimiter()

    def _dispatch(*args):
        return

    @property
    def open(self):
        return not self.socket.closed

    def is_ratelimited(self):
        return self._rate_limiter.is_ratelimited()

    @classmethod
    async def from_client(cls, client, *, initial=False, gateway=None, shard_id=None, session=None, sequence=None, resume=False):
        """Creates a main websocket for Discord from a :class:`Client`.
        This is for internal use only.
        """
        gateway = gateway or await client.http.get_gateway()
        socket = await client.http.ws_connect(gateway)
        ws = cls(socket, loop=client.loop)

        # dynamically add attributes needed
        ws.token = client.http.token
        ws._connection = client._connection
        ws._discord_parsers = client._connection.parsers
        ws._dispatch = client.dispatch
        ws.gateway = gateway
        ws.call_hooks = client._connection.call_hooks
        ws._initial_identify = initial
        ws.shard_id = shard_id
        ws._rate_limiter.shard_id = shard_id
        ws.shard_count = client._connection.shard_count
        ws.session_id = session
        ws.sequence = sequence
        ws._max_heartbeat_timeout = client._connection.heartbeat_timeout

        client._connection._update_references(ws)

        log.debug('Created websocket connected to %s', gateway)

        # poll event for OP Hello
        await ws.poll_event()

        if not resume:
            await ws.identify()
            return ws

        await ws.resume()
        return ws

    def wait_for(self, event, predicate, result=None):
        """Waits for a DISPATCH'd event that meets the predicate.
        Parameters
        -----------
        event: :class:`str`
            The event name in all upper case to wait for.
        predicate
            A function that takes a data parameter to check for event
            properties. The data parameter is the 'd' key in the JSON message.
        result
            A function that takes the same data parameter and executes to send
            the result to the future. If ``None``, returns the data.
        Returns
        --------
        asyncio.Future
            A future to wait for.
        """

        future = self.loop.create_future()
        entry = EventListener(event=event, predicate=predicate, result=result, future=future)
        self._dispatch_listeners.append(entry)
        return future

    async def identify(self):
        """Sends the IDENTIFY packet."""
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'discord.py',
                    '$device': 'discord.py',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                'compress': True,
                'large_threshold': 250,
                'v': 3
            }
        }

        if self.shard_id is not None and self.shard_count is not None:
            payload['d']['shard'] = [self.shard_id, self.shard_count]

        state = self._connection
        if state._activity is not None or state._status is not None:
            payload['d']['presence'] = {
                'status': state._status,
                'game': state._activity,
                'since': 0,
                'afk': False
            }

        if state._intents is not None:
            payload['d']['intents'] = state._intents.value

        await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
        await self.send_as_json(payload)
        log.info('Shard ID %s has sent the IDENTIFY payload.', self.shard_id)

    async def resume(self):
        """Sends the RESUME packet."""
        payload = {
            'op': self.RESUME,
            'd': {
                'seq': self.sequence,
                'session_id': self.session_id,
                'token': self.token
            }
        }

        await self.send_as_json(payload)
        log.info('Shard ID %s has sent the RESUME payload.', self.shard_id)

    async def received_message(self, msg):
        self._dispatch('socket_raw_receive', msg)

        if type(msg) is bytes:
            self._buffer.extend(msg)

            if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                return
            msg = self._zlib.decompress(self._buffer)
            msg = msg.decode('utf-8')
            self._buffer = bytearray()
        msg = json.loads(msg)

        log.debug('For Shard ID %s: WebSocket Event: %s', self.shard_id, msg)
        self._dispatch('socket_response', msg)

        op = msg.get('op')
        data = msg.get('d')
        seq = msg.get('s')
        if seq is not None:
            self.sequence = seq

        if self._keep_alive:
            self._keep_alive.tick()

        if op != self.DISPATCH:
            if op == self.RECONNECT:
                # "reconnect" can only be handled by the Client
                # so we terminate our connection and raise an
                # internal exception signalling to reconnect.
                log.debug('Received RECONNECT opcode.')
                await self.close()
                raise ReconnectWebSocket(self.shard_id)

            if op == self.HEARTBEAT_ACK:
                if self._keep_alive:
                    self._keep_alive.ack()
                return

            if op == self.HEARTBEAT:
                if self._keep_alive:
                    beat = self._keep_alive.get_payload()
                    await self.send_as_json(beat)
                return

            if op == self.HELLO:
                interval = data['heartbeat_interval'] / 1000.0
                self._keep_alive = KeepAliveHandler(ws=self, interval=interval, shard_id=self.shard_id)
                # send a heartbeat immediately
                await self.send_as_json(self._keep_alive.get_payload())
                self._keep_alive.start()
                return

            if op == self.INVALIDATE_SESSION:
                if data is True:
                    await self.close()
                    raise ReconnectWebSocket(self.shard_id)

                self.sequence = None
                self.session_id = None
                log.info('Shard ID %s session has been invalidated.', self.shard_id)
                await self.close(code=1000)
                raise ReconnectWebSocket(self.shard_id, resume=False)

            log.warning('Unknown OP code %s.', op)
            return

        event = msg.get('t')

        if event == 'READY':
            self._trace = trace = data.get('_trace', [])
            self.sequence = msg['s']
            self.session_id = data['session_id']
            # pass back shard ID to ready handler
            data['__shard_id__'] = self.shard_id
            log.info('Shard ID %s has connected to Gateway: %s (Session ID: %s).',
                     self.shard_id, ', '.join(trace), self.session_id)

        elif event == 'RESUMED':
            self._trace = trace = data.get('_trace', [])
            # pass back the shard ID to the resumed handler
            data['__shard_id__'] = self.shard_id
            log.info('Shard ID %s has successfully RESUMED session %s under trace %s.',
                     self.shard_id, self.session_id, ', '.join(trace))

        try:
            func = self._discord_parsers[event]
        except KeyError:
            log.debug('Unknown event %s.', event)
        else:
            func(data)

            # remove the dispatched listeners
            removed = []
            for index, entry in enumerate(self._dispatch_listeners):
                if entry.event != event:
                    continue

                future = entry.future
                if future.cancelled():
                    removed.append(index)
                    continue

                try:
                    valid = entry.predicate(data)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(index)
                else:
                    if valid:
                        ret = data if entry.result is None else entry.result(data)
                        future.set_result(ret)
                        removed.append(index)

            for index in reversed(removed):
                del self._dispatch_listeners[index]

    @property
    def latency(self):
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds."""
        cdef object heartbeat = self._keep_alive
        return float('inf') if heartbeat is None else heartbeat.latency

    cdef bint _can_handle_close(self):
        cdef signed int code = self._close_code or self.socket.close_code
        return code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014)

    async def poll_event(self):
        """Polls for a DISPATCH event and handles the general gateway loop.
        Raises
        ------
        ConnectionClosed
            The websocket connection was terminated for unhandled reasons.
        """
        try:
            msg = await self.socket.receive(timeout=self._max_heartbeat_timeout)
            if msg.type is aiohttp.WSMsgType.TEXT:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.BINARY:
                await self.received_message(msg.data)
            elif msg.type is aiohttp.WSMsgType.ERROR:
                log.debug('Received %s', msg)
                raise msg.data
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                log.debug('Received %s', msg)
                raise WebSocketClosure
        except (asyncio.TimeoutError, WebSocketClosure) as e:
            # Ensure the keep alive handler is closed
            if self._keep_alive:
                self._keep_alive.stop()
                self._keep_alive = None

            if isinstance(e, asyncio.TimeoutError):
                log.info('Timed out receiving packet. Attempting a reconnect.')
                raise ReconnectWebSocket(self.shard_id) from None

            code = self._close_code or self.socket.close_code
            if self._can_handle_close():
                log.info('Websocket closed with %s, attempting a reconnect.', code)
                raise ReconnectWebSocket(self.shard_id) from None
            else:
                log.info('Websocket closed with %s, cannot reconnect.', code)
                raise ConnectionClosed(self.socket, shard_id=self.shard_id, code=code) from None

    async def send(self, data):
        await self._rate_limiter.block()
        self._dispatch('socket_raw_send', data)
        await self.socket.send_str(data)

    async def send_as_json(self, data):
        try:
            await self.send(utils.to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket, shard_id=self.shard_id) from exc

    async def send_heartbeat(self, data):
        # This bypasses the rate limit handling code since it has a higher priority
        try:
            await self.socket.send_str(utils.to_json(data))
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket, shard_id=self.shard_id) from exc

    async def change_presence(self, *, activity=None, status=None, afk=False, since=0.0):
        if activity is not None:
            if not isinstance(activity, BaseActivity):
                raise InvalidArgument('activity must derive from BaseActivity.')
            activity = activity.to_dict()

        if status == 'idle':
            since = int(time.time() * 1000)

        payload = {
            'op': self.PRESENCE,
            'd': {
                'activities': [activity],
                'afk': afk,
                'since': since,
                'status': status
            }
        }

        sent = utils.to_json(payload)
        log.debug('Sending "%s" to change status', sent)
        await self.send(sent)

    async def request_chunks(self, guild_id, query=None, *, limit, user_ids=None, presences=False, nonce=None):
        payload = {
            'op': self.REQUEST_MEMBERS,
            'd': {
                'guild_id': guild_id,
                'presences': presences,
                'limit': limit
            }
        }

        if nonce:
            payload['d']['nonce'] = nonce

        if user_ids:
            payload['d']['user_ids'] = user_ids

        if query is not None:
            payload['d']['query'] = query


        await self.send_as_json(payload)

    async def voice_state(self, guild_id, channel_id, self_mute=False, self_deaf=False):
        payload = {
            'op': self.VOICE_STATE,
            'd': {
                'guild_id': guild_id,
                'channel_id': channel_id,
                'self_mute': self_mute,
                'self_deaf': self_deaf
            }
        }

        log.debug('Updating our voice state to %s.', payload)
        await self.send_as_json(payload)

    async def close(self, code=4000):
        if self._keep_alive:
            self._keep_alive.stop()
            self._keep_alive = None

        self._close_code = code
        await self.socket.close(code=code)
