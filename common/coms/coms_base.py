import inspect
import json
import logging
from typing import Any

from pydantic import ValidationError, create_model, validate_arguments

from common.coms.errors import InvalidPacketReceived
from common.coms.packet import VALID_PACKET_DATA_TYPES, Packet
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType

EXCLUDED_ANNOS = {"self", "return"}


class ComsBase:
    def __init__(
        self,
        host: str,
        port: int,
        packet_handlers: dict[PacketType, PacketHandler],
        logger: logging.Logger,
    ):
        self.host = host
        self.port = port
        self.packet_handlers = packet_handlers
        self.logger = logger

    def _decode(self, message: str | bytes) -> Packet:
        data: Any
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            raise InvalidPacketReceived("packet was not a JSON object", e)

        if not isinstance(data, dict):
            raise InvalidPacketReceived("packet was not a JSON object")

        try:
            return Packet(**data)
        except (ValidationError, ValueError, TypeError) as e:
            raise InvalidPacketReceived("could not construct Packet model", e)

    async def _call_handler(self, packet: Packet) -> dict[str, VALID_PACKET_DATA_TYPES]:
        handler = self.packet_handlers.get(packet.type)

        if handler is None:
            self.logger.error("Missing packet handler for packet type %s", packet.type)
            return

        response = await validate_arguments(handler.function)(**packet.data)

        if not isinstance(response, VALID_PACKET_DATA_TYPES):
            raise ValueError(
                f"Packet handler {handler.function.__qualname__} returned an unsupported type: {type(response)!r}"
            )

        return response

    # async def _call_handler(self, packet: Packet) -> dict[str, VALID_PACKET_DATA_TYPES]:
    #     handler = self.packet_handlers.get(packet.type)

    #     if handler is None:
    #         self.logger.error("Missing packet handler for packet type %s", packet.type)
    #         return

    #     annos = {k: getattr(v, "__origin__", v) for k, v in handler.__annotations__.items()}
    #     annos.pop("return", None)
    #     annos.pop("self", None)

    #     # check for missing args or incorrect arg types
    #     for arg, arg_type in annos.items():
    #         if arg not in packet.data:
    #             raise ValueError(
    #                 f"Argument {arg!r} of packet handler {handler.function.__qualname__} was not present in the packet"
    #             )

    #         if not isinstance((arg_value := packet.data[arg]), arg_type):
    #             raise TypeError(
    #                 f"Argument {arg!r} of packet handler {handler.function.__qualname__} received an invalid type: {type(arg_value)!r}"
    #             )

    #     # check for extra args
    #     for arg in packet.data.keys():
    #         if arg not in annos:
    #             raise TypeError(
    #                 f"Packet handler {handler.function.__qualname__} received an extra argument: {arg!r}"
    #             )

    #     response = await handler(**packet.data)

    #     if not isinstance(response, VALID_PACKET_DATA_TYPES):
    #         raise ValueError(
    #             f"Packet handler {handler.function.__qualname__} returned an unsupported type: {type(response)!r}"
    #         )

    #     return response
