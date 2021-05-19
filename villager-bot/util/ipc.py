from classyjson import ClassyDict
from typing import Union
import asyncio
import struct
import orjson

LENGTH_LENGTH = struct.calcsize(">i")


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

        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def read_packet(self) -> ClassyDict:
        length = await self.reader.read(LENGTH_LENGTH)  # read the length of the upcoming packet
        data = await self.reader.read(length)  # read the rest of the packet

        return ClassyDict(orjson.loads(data))

    async def send_packet(self, data: Union[dict, ClassyDict]):
        data = orjson.dumps(data)  # orjson dumps to bytes
        packet = struct.pack(">i", len(data)) + data

        self.writer.write(packet)
        await self.writer.drain()
