import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional
import uuid

from pydantic import BaseModel
from websockets.server import WebSocketServerProtocol, serve, WebSocketServer
from websockets.exceptions import ConnectionClosedOK as WebSocketConnectionClosedOK

from common.coms.coms_base import ComsBase
from common.coms.errors import InvalidPacketReceived, NoConnectedClientsError
from common.coms.packet import T_PACKET_DATA, Packet
from common.coms.packet_handling import PacketHandler, PacketType


class Broadcast(BaseModel):
    ready: asyncio.Event
    ws_ids: set[uuid.UUID]  # ws ids to expect a response from
    responses: list[T_PACKET_DATA]

    class Config:
        arbitrary_types_allowed = True


class Server(ComsBase):
    def __init__(
        self,
        host: str,
        port: int,
        auth: str,
        packet_handlers: dict[PacketType, PacketHandler],
        logger: logging.Logger,
        connect_cb: Optional[Callable[[uuid.UUID], Coroutine[None, Any, Any]]] = None,
        disconnect_cb: Optional[Callable[[uuid.UUID], Coroutine[None, Any, Any]]] = None,
    ):
        super().__init__(host, port, packet_handlers, logger.getChild("server"))

        self.auth = auth

        self.connect_cb = connect_cb
        self.disconnect_cb = disconnect_cb

        self._stop = asyncio.Event()
        self._connections = list[WebSocketServerProtocol]()  # only authed connections
        self._current_id = 0
        self._broadcasts = dict[str, Broadcast]()
        self._server: Optional[WebSocketServer] = None

    def _get_packet_id(self, t: str = "s") -> str:
        packet_id = self._current_id
        self._current_id += 1
        return f"{t}{packet_id}"

    async def serve(self, ready_cb: Optional[Callable[[], None]] = None) -> None:
        async with serve(
            self._handle_connection, self.host, self.port, logger=self.logger.getChild("ws")
        ) as self._server:
            if ready_cb is not None:
                ready_cb()

            await self._stop.wait()            

    async def stop(self) -> None:
        if self._connections:
            await asyncio.wait([c.drain() for c in self._connections])

        self._stop.set()

    async def _send(self, ws: WebSocketServerProtocol, packet: Packet) -> None:
        await ws.send(packet.json())

    async def _disconnect(self, ws: WebSocketServerProtocol) -> None:
        if not ws.closed:
            await ws.close()

        try:
            self._connections.remove(ws)
        except ValueError:
            pass

        self.logger.info("Disconnected client: %s", ws.id)

        if self.disconnect_cb:
            asyncio.create_task(self.disconnect_cb(ws.id))

    async def raw_broadcast(self, packet_type: PacketType, packet_data: T_PACKET_DATA = None) -> None:
        packet = Packet(id=self._get_packet_id("b"), type=packet_type, data=packet_data)
        coros = [self._send(c, packet) for c in self._connections]
        await asyncio.wait(coros)

    async def broadcast(
        self, packet_type: PacketType, packet_data: T_PACKET_DATA = None
    ) -> list[T_PACKET_DATA]:
        if len(self._connections) == 0:
            raise NoConnectedClientsError()

        broadcast_id = self._get_packet_id("b")
        broadcast_packet = Packet(id=broadcast_id, type=packet_type, data=packet_data)

        ws_ids = {ws.id for ws in self._connections}
        broadcast_coros = [
            self._send(c, broadcast_packet) for c in self._connections if c.id in ws_ids
        ]
        broadcast = self._broadcasts[broadcast_id] = Broadcast(
            ready=asyncio.Event(), ws_ids=ws_ids, responses=[]
        )

        await asyncio.wait(broadcast_coros)
        await broadcast.ready.wait()

        return broadcast.responses

    async def _client_broadcast(self, ws: WebSocketServerProtocol, packet: Packet) -> None:
        assert isinstance(packet.data, dict)

        responses = await self.broadcast(packet.data["type"], packet.data["data"])

        # send response back to client who requested broadcast
        await self._send(ws, Packet(id=packet.id, data=responses))

    async def _handle_broadcast_response(self, ws: WebSocketServerProtocol, packet: Packet) -> None:
        broadcast = self._broadcasts[packet.id]

        if ws.id not in broadcast.ws_ids:
            raise RuntimeError(
                f"Unexpected response from websocket {ws.id} for broadcast {packet.id}",
            )

        broadcast.responses.append(packet.data)
        broadcast.ws_ids.remove(ws.id)

        if len(broadcast.ws_ids) == 0:
            broadcast.ready.set()

    async def _handle_connection(self, ws: WebSocketServerProtocol):
        self.logger.info("New client connected: %s", ws.id)

        authed = False

        try:
            async for message in ws:
                try:
                    packet = self._decode(message)
                except InvalidPacketReceived:
                    self.logger.error(
                        "Invalid packet received from client: %s", ws.id, exc_info=True
                    )
                    await self._disconnect(ws)
                    return

                if packet.type == PacketType.AUTH:
                    if authed:
                        self.logger.error(
                            "Already received authorization packet from client: %s", ws.id
                        )
                        await self._disconnect(ws)
                        return

                    if packet.data != self.auth:
                        self.logger.error("Incorrect authorization received from client: %s", ws.id)
                        await self._disconnect(ws)
                        return

                    self._connections.append(ws)
                    authed = True

                    if self.connect_cb:
                        asyncio.create_task(self.connect_cb(ws.id))

                    continue

                if not authed:
                    self.logger.error(
                        "Authorization packet was not the first received from client: %s", ws.id
                    )
                    await self._disconnect(ws)
                    return

                # handle broadcast requests
                if packet.type == PacketType.BROADCAST_REQUEST:
                    # broadcast requests are special types of packets which forward the packet to ALL connected clients
                    asyncio.create_task(
                        self._client_broadcast(ws, packet)
                    )  # TODO: keep track of these tasks and properly cancel them on a server shutdown
                    continue

                # handle broadcast responses
                if packet.id in self._broadcasts:
                    await self._handle_broadcast_response(ws, packet)
                    continue

                try:
                    response = await self._call_handler(packet, ws_id=ws.id)
                except Exception as e:
                    self.logger.error(
                        "An error ocurred while calling the packet handler for packet %s",
                        packet,
                        exc_info=True,
                    )
                    await self._send(ws, Packet(id=packet.id, data=repr(e), error=True))
                else:
                    await self._send(ws, Packet(id=packet.id, data=response))
        except WebSocketConnectionClosedOK:
            pass
        finally:
            await self._disconnect(ws)
