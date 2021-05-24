from asyncio import StreamReader, StreamWriter
from typing import Union, Callable
from classyjson import ClassyDict
import asyncio
import struct
import orjson

LENGTH_LENGTH = struct.calcsize(">i")

# Basically this protocol revolves around sending json data. A packet consists of the length
# of the upcoming data to read as a big endian int32 (i) as well as the data itself, dumped to
# a string and then encoded into UTF8.
#
# Example:
# >>> data = "123 abcd test"
# >>> data_encoded = data.encode("utf8")
# >>> struct.pack(">i", len(data_encoded)) + data_encoded
# b'\x00\x00\x00\r123 abcd test'
#
# The JSON payload is expected to have a "type" field, which helps the server know what to do with
# the packet. In addition, packets sent by the Client include an "auth" field, which contains the
# authorization code. Authorization should be automatically validated by the Server class, and
# automatically added by the Client class.
#
# Examples:
# {"type": "identify", "shard_id": 123} # client -> server
# {"type": "exec-code", "code": "print('hello')", "auth": "password123"} # client -> server
# {"type": "exec-response", "response": "None"} # server -> client
#
# Packet Documentation:
# Serverbound:
# - shard-ready {"type": "shard-ready", "shard_id": shard_id} notifies karen of a shard becoming ready
# - shard-disconnect {"type": "shard-disconnect", "shard_id": shard_id} notifies karen of shard disconnect
# - eval {"type": "eval", "code": code} eval()s code on karen
# - broadcast-request {"type": "broadcast-request", "packet": encapsulated_packet} broadcasts a packet to all clients, including the sender
# - broadcast-response {"type": "broadcast-response", **} sent in response to any "unexpected" packet from karen (so the contents of broadcast packets)
# - cooldown {"type": "cooldown", "command": command_name, "user_id", user.id} requests and updates cooldown info from karen
# Clientbound:
# - eval-response {"type": "eval-response", "result": object, "success": boolean} the result of an eval packet from a client
# - broadcast-response {"type": "broadcast-response", "responses": [*]} the result of a client's broadcast-request
# - cooldown-info {"type": "cooldown-info", "can_run": boolean, Optional["remaining": cooldown_seconds_remaining]} the result of a client's cooldown packet


def default_serialize(obj):
    return repr(obj)


class Stream:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read_packet(self) -> ClassyDict:
        (length,) = struct.unpack(">i", await self.reader.read(LENGTH_LENGTH))  # read the length of the upcoming packet
        data = await self.reader.read(length)  # read the rest of the packet

        return ClassyDict(orjson.loads(data))

    async def write_packet(self, data: Union[dict, ClassyDict]) -> None:
        data = orjson.dumps(data, default=default_serialize)  # orjson dumps to bytes
        packet = struct.pack(">i", len(data)) + data

        if len(packet) > 65535:
            raise ValueError("Packet is too big to send...")

        self.writer.write(packet)
        await self.writer.drain()

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()


class Client:
    def __init__(self, host: str, port: int, handle_broadcast: Callable) -> None:
        self.host = host
        self.port = port

        self.handle_broadcast = handle_broadcast

        self.stream = None

        self.expected_packets = {}  # packet_id: [asyncio.Event, Union[Packet, None]]
        self.current_id = 0
        self.read_task = None

    async def connect(self, auth: str, shard_ids: tuple) -> None:
        self.stream = Stream(*await asyncio.open_connection(self.host, self.port))
        self.read_task = asyncio.create_task(self.read_packets())

        res = await self.request({"type": "auth", "auth": auth})

        if not res.success:
            self.read_task.cancel()
            await self.stream.close()

            raise Exception("Invalid authorization")

    async def close(self) -> None:
        self.read_task.cancel()

        await self.send({"type": "disconnect"})
        await self.stream.close()

    async def read_packets(self):
        while True:
            packet = await self.stream.read_packet()

            if packet.id in self.expected_packets:
                self.expected_packets[packet.id][1] = packet
                self.expected_packets[packet.id][0].set()
            else:
                asyncio.create_task(self.handle_broadcast(packet))

    async def send(self, packet: Union[dict, ClassyDict]) -> None:
        await self.stream.write_packet(packet)

    async def request(self, packet: Union[dict, ClassyDict]) -> ClassyDict:
        packet["id"] = packet_id = f"c{self.current_id}"
        self.current_id += 1

        # create entry before sending packet
        event = asyncio.Event()
        self.expected_packets[packet_id] = [event, None]

        await self.send(packet)  # send packet off to karen

        await event.wait()  # wait for response event
        return self.expected_packets[packet_id][1]  # return received packet

    async def broadcast(self, packet: Union[dict, ClassyDict]) -> ClassyDict:
        return await self.request({"type": "broadcast-request", "packet": packet})


class Server:
    def __init__(self, host: str, port: int, auth: str, handle_packet: Callable) -> None:
        self.host = host
        self.port = port

        self.auth = auth

        self.handle_packet = handle_packet

        self.server = None
        self.serve_task = None

        self.connections = []

        self.closing = False

    async def start(self) -> None:
        self.server = await asyncio.start_server(self.handle_connection, self.host, self.port)
        self.serve_task = asyncio.create_task(self.server.serve_forever())

    async def serve(self) -> None:
        await self.serve_task
        self.closing = True

    async def close(self) -> None:
        self.closing = True
        self.serve_task.cancel()

        self.server.close()
        await self.server.wait_closed()

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        stream = Stream(reader, writer)
        self.connections.append(stream)
        authed = False

        while not self.closing:
            packet = await stream.read_packet()

            if not authed:
                auth = packet.get("auth", None)

                if auth == self.auth:
                    authed = True
                    await stream.write_packet({"type": "auth-response", "success": True, "id": packet.id})
                else:
                    await stream.write_packet({"type": "auth-response", "success": False, "id": packet.id})
                    return

                continue

            if packet.type == "disconnect":
                self.connections.remove(stream)
                return

            asyncio.create_task(self.handle_packet(stream, packet))
