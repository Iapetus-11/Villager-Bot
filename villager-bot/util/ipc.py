from classyjson import ClassyDict
from typing import Union
import asyncio
import struct
import orjson

LENGTH_LENGTH = struct.calcsize(">i")


class Stream(asyncio.StreamWriter):
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        super().__init__(writer._transport, writer._protocol, writer._reader, writer._loop)

    def read(self, n: int = -1) -> bytes:
        return self._reader.read(n)

    def readline(self) -> bytes:
        return self._reader.readline()

    def readexactly(self, n: int) -> bytes:
        return self._reader.readexactly(n)

    def readuntil(self, separator: bytes = b"\n") -> bytes:
        return self._reader.readuntil(separator)


class Connection:
    """
    The Connection class used for IPC, communicates via the 69 protocol, as described below.

    Basically this protocol revolves around sending json data. A packet consists of the length
    of the upcoming data to read as a big endian int32 (i) as well as the data itself, dumped to a string
    and then encoded into UTF8.

    Example:
    >>> data = "123 abcd test"
    >>> data_encoded = data.encode("utf8")
    >>> struct.pack(">i", len(data_encoded)) + data_encoded
    b'\x00\x00\x00\r123 abcd test'
    """

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

        self.stream = None

    async def connect(self):
        self.stream = Stream(*await asyncio.open_connection(self.host, self.port))

    async def close(self):
        self.stream.close()
        await self.stream.wait_closed()

    async def read_packet(self) -> ClassyDict:
        length = await self.stream.read(LENGTH_LENGTH)  # read the length of the upcoming packet
        data = await self.stream.read(length)  # read the rest of the packet

        return ClassyDict(orjson.loads(data))

    async def send_packet(self, data: Union[dict, ClassyDict]):
        data = orjson.dumps(data)  # orjson dumps to bytes
        packet = struct.pack(">i", len(data)) + data

        self.stream.write(packet)
        await self.stream.drain()
