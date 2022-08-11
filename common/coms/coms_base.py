import json
import logging
from typing import Any

from pydantic import ValidationError, validate_arguments

from common.coms.errors import InvalidPacketReceived
from common.coms.packet import PACKET_DATA_TYPES, T_PACKET_DATA, Packet
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType


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

    async def _call_handler(self, packet: Packet, **extra: Any) -> T_PACKET_DATA:
        if packet.type is None:
            raise ValueError(f"Missing packet type for packet {packet}")

        handler = self.packet_handlers.get(packet.type)

        if handler is None:
            self.logger.error("Missing packet handler for packet type %s", packet.type)
            raise ValueError(f"Missing packet handler for packet type {packet.type.name}")

        # remove any **extra keys/values which aren't expected by the handler function
        for extra_k in list(extra.keys()):
            if extra_k not in handler.function.__annotations__:
                del extra[extra_k]

        handler_args = []
        handler_kwargs = {}

        if isinstance(packet.data, dict):
            handler_kwargs = packet.data
        else:
            handler_args.append(packet.data)

        response = await validate_arguments(handler.function)(
            *handler_args, **handler_kwargs, **extra
        )

        if not isinstance(response, PACKET_DATA_TYPES):
            raise ValueError(
                f"Packet handler {handler.function.__qualname__} returned an unsupported type: {type(response)!r}"
            )

        return response
