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


class Stream:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read_packet(self) -> ClassyDict:
        (length,) = struct.unpack(">i", await self.reader.read(LENGTH_LENGTH))  # read the length of the upcoming packet
        data = await self.reader.read(length)  # read the rest of the packet

        return ClassyDict(orjson.loads(data))

    async def write_packet(self, data: Union[dict, ClassyDict]) -> None:
        data = orjson.dumps(data)  # orjson dumps to bytes
        packet = struct.pack(">i", len(data)) + data

        self.writer.write(packet)
        await self.writer.drain()

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()


class Client:
    def __init__(self, host: str, port: int, auth: str) -> None:
        self.host = host
        self.port = port

        self.auth = auth

        self.stream = None

        self.received = []
        self.cur_id = 0

    async def connect(self, shard_ids: tuple) -> None:
        self.stream = Stream(*await asyncio.open_connection(self.host, self.port))

    async def close(self) -> None:
        await self.write_packet({"type": "disconnect"})
        await self.stream.close()

    async def read_packet(self) -> ClassyDict:
        try:
            return self.received.pop()
        except IndexError:
            return await self.stream.read_packet()

    async def write_packet(self, data: Union[dict, ClassyDict]) -> int:
        data["auth"] = self.auth
        id = data["id"] = self.cur_id
        self.cur_id += 1

        await self.stream.write_packet(data)

        return id

    async def request_packet(self, data: Union[dict, ClassyDict]):
        id = await self.write_packet(data)

        while True:
            packet = await self.read_packet()

            if packet.get("id") == id:
                return packet

            self.received.append(packet)

            await asyncio.sleep(0.1)  # sleep to avoid infinite blocking loop


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

        while not self.closing:
            packet = await stream.read_packet()

            # check auth, if invalid notify client and ignore subsequent requests
            if packet.pop("auth", None) != self.auth:
                await stream.send_packet({"info": "invalid authorization"})
                return

            if packet.type == "disconnect":
                self.connections.remove(stream)
                return

            await self.handle_packet(stream, packet)
