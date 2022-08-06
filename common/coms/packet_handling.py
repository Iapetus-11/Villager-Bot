from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, TypeAlias

from common.coms.packet import VALID_PACKET_DATA_TYPES
from common.coms.packet_type import PacketType

T_PACKET_HANDLER_CALLABLE: TypeAlias = Callable[..., Awaitable[dict[str, Any] | None]]
T_HANDLER_CALLABLE_REGISTRY: TypeAlias = dict[PacketType, T_PACKET_HANDLER_CALLABLE]


class PacketHandler:
    __slots__ = ("packet_type", "function")

    def __init__(self, packet_type: PacketType, function: T_PACKET_HANDLER_CALLABLE):
        self.packet_type = packet_type
        self.function = function

    def __call__(self, packet: dict[str, Any]) -> Optional[dict[str, Any]]:
        return self.function(**packet)


def validate_packet_handler_function(function: T_PACKET_HANDLER_CALLABLE) -> None:
    # check if any args are missing annotations
    if any([arg_name not in function.__annotations__ for arg_name in function.__code__.co_varnames]):
        raise ValueError(
            f"The packet handler {function.__qualname__} is missing argument annotations / typehints for one or more arguments"
        )

    # check if typehints are actually json compatible
    annos = {k: getattr(v, "__origin__", v) for k, v in function.__annotations__.items()}
    annos.pop("return", None)
    annos.pop("self", None)
    for arg, arg_type in annos.items():
        if not isinstance(arg_type, type) or not issubclass(arg_type, VALID_PACKET_DATA_TYPES):
            raise ValueError(
                f"Argument {arg!r} of the packet handler {function.__qualname__} has an unsupported annotation / typehint: {arg_type!r}"
            )


def handle_packet(packet_type: PacketType) -> Callable[[T_PACKET_HANDLER_CALLABLE], PacketHandler]:
    """Decorator for creating a PacketHandler object in a class"""

    def _inner(handler: T_PACKET_HANDLER_CALLABLE) -> PacketHandler:
        return PacketHandler(packet_type, handler)

    return _inner


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

    def __new__(cls, *args, **kwargs) -> PacketHandlerRegistry:
        self = super().__new__(cls)

        # bind handlers to their class instance manually
        for packet_type, handler in list(cls.__packet_handlers__.items()):
            self.__packet_handlers__[packet_type] = handler.__get__(self)

        return self

    def get_packet_handlers(self) -> T_HANDLER_CALLABLE_REGISTRY:
        return self.__packet_handlers__
