from asyncio imoprt StreamReader, StreamWriter
from classyjson import ClassyDict
from typing import Union
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
# the packet. The current available types are "info", "exec", "fetch", "store", "close". In addition,
# packets sent by the Client include an "auth" field, which contains the authorization code.
# Authorization should be automatically validated by the Server class, and automatically added by
# the Client class.
#
# Packet Types:
# - exec-code - exec/eval the code given in the "code" field
# - exec-response - the response of executing the code from exec-code
# - fetch - fetches data, more info later
# - store - stores data, more info later
#
# Example:
# {"type": "exec-code", "code": "print('hello')", "auth": "password123"} # client -> server
# {"type": "exec-response", "response": "None"} # server -> client


class Stream:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read_packet(self) -> ClassyDict:
        length = await self.reader.read(LENGTH_LENGTH)  # read the length of the upcoming packet
        data = await self.reader.read(length)  # read the rest of the packet

        return ClassyDict(orjson.loads(data))

    async def write_packet(self, data: Union[dict, ClassyDict]) -> None:
        data = orjson.dumps(data)  # orjson dumps to bytes
        packet = struct.pack(">i", len(data)) + data

        self.writer.write(packet)
        await self.writer.drain()

    async def close(self) ->  None:
        self.writer.close()
        await self.writer.wait_closed()


class Client:
    """The Client class used for IPC, communicates via the 69 protocol, as described above."""

    def __init__(self, host: str, port: int, auth: str) -> None:
        self.host = host
        self.port = port
        self.auth = auth

        self.stream = None

    async def connect(self) -> None:
        self.stream = Stream(*await asyncio.open_connection(self.host, self.port))

    async def close(self) -> None:
        await self.stream.close()

    async def read_packet(self) -> ClassyDict:
        return await self.stream.read_packet()

    async def write_packet(self, data: Union[dict, ClassyDict]) -> None:
        data["auth"] = self.auth
        await self.stream.write_packet(data)


class Server:
    def __init__(self, host: str, port: int, auth: str) -> None:
        self.host = host
        self.port = port
        self.auth = auth

        self.server = None
        self.serve_task = None

    async def start(self) -> None:
        self.server = await asyncio.start_server(self.on_connection, self.host, self.port)
        self.serve_task = asyncio.create_task(self.server.serve_forever())

    async def serve(self) -> None:
        await self.serve_task

    async def close(self) -> None:
        self.serve_task.cancel()

        self.server.close()
        await self.server.wait_closed()

    async def on_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        stream = Stream(reader, writer)

        while True:
            data = await stream.read_packet()

            # check auth, if invalid notify client and ignore subsequent requests
            if data.pop("auth", None) != self.auth:
                await stream.send_packet({"info": "invalid authorization"})
                return
