from typing import Awaitable, Dict, Optional, Union, Callable
from asyncio import StreamReader, StreamWriter
from enum import IntEnum, auto
import classyjson as cj
import asyncio
import struct

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
# The JSON payload is expected to have a "type" field as well as an "id", which helps
# the receiver to know what to do with the packet. The first packet from the client
# must be an authorization packet containing the pre-shared secret.


class PacketType(IntEnum):
    AUTH = auto()
    AUTH_RESPONSE = auto()
    DISCONNECT = auto()
    MISSING_PACKET = auto()
    CLUSTER_READY = auto()
    EVAL = auto()
    EVAL_RESPONSE = auto()
    EXEC = auto()
    EXEC_RESPONSE = auto()
    BROADCAST_REQUEST = auto()
    BROADCAST_RESPONSE = auto()
    COOLDOWN = auto()
    COOLDOWN_RESPONSE = auto()
    COOLDOWN_ADD = auto()
    COOLDOWN_RESET = auto()
    DM_MESSAGE = auto()
    DM_MESSAGE_REQUEST = auto()
    MINE_COMMAND = auto()
    MINE_COMMAND_RESPONSE = auto()
    MINE_COMMANDS_RESET = auto()
    CONCURRENCY_CHECK = auto()
    CONCURRENCY_CHECK_RESPONSE = auto()
    CONCURRENCY_ACQUIRE = auto()
    CONCURRENCY_RELEASE = auto()
    COMMAND_RAN = auto()
    ACQUIRE_PILLAGE_LOCK = auto()
    ACQUIRE_PILLAGE_LOCK_RESPONSE = auto()
    RELEASE_PILLAGE_LOCK = auto()
    PILLAGE = auto()
    REMINDER = auto()
    FETCH_STATS = auto()
    STATS_RESPONSE = auto()
    TRIVIA = auto()
    UPDATE_SUPPORT_SERVER_ROLES = auto()
    RELOAD_DATA = auto()


T_PACKET_HANDLER_CALLABLE = Callable[[cj.ClassyDict], Awaitable[Optional[dict]]]
T_HANDLER_CALLABLE_REGISTRY = Dict[PacketType, T_PACKET_HANDLER_CALLABLE]


class CustomJSONEncoder(cj.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):  # add support for sets
            return dict(_set_object=list(obj))
        else:
            return cj.JSONEncoder.default(self, obj)


def special_obj_hook(dct):
    if "_set_object" in dct:
        return set(dct["_set_object"])

    return dct


class JsonPacketStream:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

        self.drain_lock = asyncio.Lock()

    async def read_packet(self) -> cj.ClassyDict:
        (length,) = struct.unpack(">i", await self.reader.readexactly(LENGTH_LENGTH))  # read the length of the upcoming packet

        data = await self.reader.readexactly(length)

        return cj.loads(data, object_hook=special_obj_hook)

    async def write_packet(self, data: Union[dict, cj.ClassyDict]) -> None:
        data = cj.dumps(data, cls=CustomJSONEncoder).encode()
        packet = struct.pack(">i", len(data)) + data

        for i in range(0, len(packet), 65535):
            self.writer.write(packet[i - 65535 : i])

        self.writer.write(packet)
        async with self.drain_lock:
            await self.writer.drain()

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()


class PacketHandler:
    __slots__ = ("packet_type", "function")

    def __init__(self, packet_type: PacketType, function: T_PACKET_HANDLER_CALLABLE):
        self.packet_type = packet_type
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


def handle_packet(packet_type: PacketType) -> Callable[[T_PACKET_HANDLER_CALLABLE], PacketHandler]:
    """Decorator for creating a PacketHandler object in a class"""

    def _handle(function: T_PACKET_HANDLER_CALLABLE) -> PacketHandler:
        return PacketHandler(packet_type, function)

    return _handle


class PacketHandlerRegistryMeta(type):
    __packet_handlers__: T_HANDLER_CALLABLE_REGISTRY

    def __new__(cls, name, bases, dct) -> "PacketHandlerRegistryMeta":
        new = super().__new__(cls, name, bases, dct)

        new.__packet_handlers__ = {}

        # traverse the method tree to find PacketHandlers to register
        for base in reversed(new.__mro__):
            for obj in base.__dict__.values():
                if isinstance(obj, PacketHandler):
                    packet_type = obj.packet_type
                    function = obj.function

                    if packet_type in new.__packet_handlers__:
                        raise ValueError(
                            f"Can't register {function.__module__}.{function.__qualname__} as a handler for packet type {packet_type} because there already is one."
                        )

                    new.__packet_handlers__[packet_type] = function

        return new


class PacketHandlerRegistry(metaclass=PacketHandlerRegistryMeta):
    __packet_handlers__: T_HANDLER_CALLABLE_REGISTRY

    def __new__(cls, *args, **kwargs) -> "PacketHandlerRegistry":
        self = super().__new__(cls)

        # bind handlers to their class instance manually
        for packet_type, handler in list(cls.__packet_handlers__.items()):
            self.__packet_handlers__[packet_type] = handler.__get__(self)

        return self

    def get_packet_handlers(self) -> T_HANDLER_CALLABLE_REGISTRY:
        return self.__packet_handlers__


class PacketPlaceholder:
    __slots__ = ("packet", "_event")

    def __init__(self):
        self.packet: cj.ClassyDict = None
        self._event = asyncio.Event()

    def set(self, packet: cj.ClassyDict) -> None:
        self.packet = packet
        self._event.set()

    async def wait(self) -> cj.ClassyDict:
        await self._event.wait()
        return self.packet

    def __repr__(self) -> str:
        return f"PacketPlaceholder(packet={self.packet!r})"

    __str__ = __repr__


class Client:
    def __init__(self, host: str, port: int, packet_handlers: Dict[PacketType, PacketHandler]):
        self.host = host
        self.port = port

        self.packet_handlers = packet_handlers

        self._stream = None

        self._expected_packets: Dict[str, PacketPlaceholder] = {}
        self._current_id = 0
        self._read_task = None

    async def connect(self, auth: str) -> None:
        self._stream = JsonPacketStream(*await asyncio.open_connection(self.host, self.port))
        self._read_task = asyncio.create_task(self._read_packets())

        res = await self.request({"type": PacketType.AUTH, "auth": auth})

        if not res.success:
            self._read_task.cancel()
            await self._stream.close()

            raise ValueError("Invalid authorization")

    async def close(self) -> None:
        self._read_task.cancel()

        await self.send({"type": PacketType.DISCONNECT})
        await self._stream.close()

    async def _read_packets(self):
        while True:
            packet = await self._stream.read_packet()

            if packet.id in self._expected_packets:
                self._expected_packets[packet.id].set(packet)
            else:
                asyncio.create_task(self._call_handler(packet))

    async def send(self, packet: Union[dict, cj.ClassyDict]) -> None:
        await self._stream.write_packet(packet)

    async def request(self, packet: Union[dict, cj.ClassyDict]) -> cj.ClassyDict:
        packet["id"] = packet_id = f"c{self._current_id}"
        self._current_id += 1

        # create entry before sending packet
        placeholder = self._expected_packets[packet_id] = PacketPlaceholder()

        await self.send(packet)  # send packet off to karen

        res = await placeholder.wait()

        del self._expected_packets[packet_id]

        return res

    async def broadcast(self, packet: Union[dict, cj.ClassyDict]) -> cj.ClassyDict:
        return await self.request({"type": PacketType.BROADCAST_REQUEST, "packet": packet})

    async def eval(self, code: str) -> cj.ClassyDict:
        return await self.request({"type": PacketType.EVAL, "code": code})

    async def exec(self, code: str) -> cj.ClassyDict:
        return await self.request({"type": PacketType.EXEC, "code": code})

    async def _call_handler(self, packet: cj.ClassyDict):
        handler = self.packet_handlers.get(packet.type)

        if handler is None:
            handler = self.packet_handlers[PacketType.MISSING_PACKET]

        data = await handler(packet)

        if isinstance(data, dict):
            if packet.get("id") is not None:
                data["id"] = packet.id

            data["type"] = PacketType.BROADCAST_RESPONSE

            await self.send(data)
        elif data is not None:
            raise ValueError(
                f"Invalid return from handler {handler.function.__module__}.{handler.function.__qualname__}: {data!r}"
            )


class Server:
    def __init__(self, host: str, port: int, auth: str, packet_handlers: Dict[PacketType, PacketHandler]):
        self.host = host
        self.port = port

        self.auth = auth

        self.packet_handlers = packet_handlers

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

    async def call_handler(self, stream: JsonPacketStream, packet: cj.ClassyDict) -> None:
        handler = self.packet_handlers.get(packet.type)

        if handler is None:
            handler = self.packet_handlers[PacketType.MISSING_PACKET]

        data = await handler(packet)

        if isinstance(data, dict):
            if packet.get("id") is not None:
                data["id"] = packet.id

            await stream.write_packet(data)
        elif data is not None:
            raise ValueError(
                f"Invalid return from handler {handler.function.__module__}.{handler.function.__qualname__}: {data!r}"
            )

    async def handle_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        stream = JsonPacketStream(reader, writer)
        self.connections.append(stream)
        authed = False

        while not self.closing:
            packet = await stream.read_packet()

            if not authed:
                auth = packet.get("auth", None)

                if auth == self.auth:
                    authed = True
                    await stream.write_packet({"type": PacketType.AUTH_RESPONSE, "success": True, "id": packet.id})
                else:
                    await stream.write_packet({"type": PacketType.AUTH_RESPONSE, "success": False, "id": packet.id})
                    self.connections.remove(stream)
                    return

                continue

            if packet.type == PacketType.DISCONNECT:
                self.connections.remove(stream)
                return

            asyncio.create_task(self.call_handler(stream, packet))
