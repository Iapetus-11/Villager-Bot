from __future__ import annotations

from typing import Awaitable, Callable, TypeAlias

from common.coms.packet import PACKET_DATA_TYPES, T_PACKET_DATA
from common.coms.packet_type import PacketType

T_PACKET_HANDLER_CALLABLE: TypeAlias = Callable[..., Awaitable[T_PACKET_DATA]]


class PacketHandler:
    __slots__ = ("packet_type", "function")

    def __init__(self, packet_type: PacketType, function: T_PACKET_HANDLER_CALLABLE):
        self.packet_type = packet_type
        self.function = function


def validate_packet_handler_function(function: T_PACKET_HANDLER_CALLABLE) -> None:
    # check if any args are missing annotations
    if any(
        [arg_name not in function.__annotations__ for arg_name in function.__code__.co_varnames]
    ):
        raise ValueError(
            f"The packet handler {function.__qualname__} is missing argument annotations / typehints for one or more arguments"
        )

    # check if typehints are actually json compatible
    annos = {k: getattr(v, "__origin__", v) for k, v in function.__annotations__.items() if k not in {"return", "self"}}

    for arg, arg_type in annos.items():
        if not isinstance(arg_type, type) or not issubclass(arg_type, PACKET_DATA_TYPES):
            raise ValueError(
                f"Argument {arg!r} of the packet handler {function.__qualname__} has an unsupported annotation / typehint: {arg_type!r}"
            )


def handle_packet(packet_type: PacketType) -> Callable[[T_PACKET_HANDLER_CALLABLE], PacketHandler]:
    """Decorator for creating a PacketHandler object in a class"""

    def _inner(handler: T_PACKET_HANDLER_CALLABLE) -> PacketHandler:
        return PacketHandler(packet_type, handler)

    return _inner


class PacketHandlerRegistryMeta(type):
    # def __new__(cls, name, bases, dct):
    #     new = super().__new__(cls, name, bases, dct)
    #     new.__packet_handlers__ = dict[PacketType, PacketHandler]()

    #     # traverse the method tree to find PacketHandlers to register
    #     for base in reversed(new.__mro__):
    #         for obj in base.__dict__.values():
    #             if isinstance(obj, PacketHandler):
    #                 if obj.packet_type in new.__packet_handlers__:
    #                     raise RuntimeError(f"Duplicate packet handler: {obj.function.__qualname__}")

    #                 new.__packet_handlers__[obj.packet_type] = obj

    #     return new

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__packet_handlers__ = dict[PacketType, PacketHandler]()

        for base in self.__mro__:
            for obj in base.__dict__.values():
                if isinstance(obj, PacketHandler):
                    if obj.packet_type in self.__packet_handlers__:
                        raise RuntimeError(f"Duplicate packet handler: {obj.function.__qualname__}")

                    self.__packet_handlers__[obj.packet_type] = obj


class PacketHandlerRegistry(metaclass=PacketHandlerRegistryMeta):
    __packet_handlers__: dict[PacketType, PacketHandler]

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)

        # bind handlers to their class instance
        for handler in self.__packet_handlers__.values():
            handler.function = handler.function.__get__(self)

        return self

    def get_packet_handlers(self) -> dict[PacketType, PacketHandler]:
        return self.__packet_handlers__
