import json
import logging
from typing import Any

from pydantic import ValidationError, validate_arguments

from common.coms.errors import InvalidPacketReceived
from common.coms.json_encoder import special_obj_decode
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
            data = json.loads(message, object_hook=special_obj_decode)
        except json.JSONDecodeError as e:
            raise InvalidPacketReceived("Packet was not a valid JSON object", e)

        if not isinstance(data, dict):
            raise InvalidPacketReceived(
                f"Packet was expected to be of type 'dict', got '{type(data).__name}' instead",
            )

        try:
            return Packet(**data)
        except (ValidationError, ValueError, TypeError) as e:
            raise InvalidPacketReceived("Could not construct Packet model", e)

    async def _call_handler(self, packet: Packet, **extra: Any) -> T_PACKET_DATA:
        if packet.type is None:
            raise ValueError(f"Missing packet type for packet {packet}")

        handler = self.packet_handlers.get(packet.type)

        if handler is None:
            self.logger.error("Missing packet handler for packet type %s", packet.type)
            raise RuntimeError(f"Missing packet handler for packet type {packet.type.name}")

        annos = {
            k: v for k, v in handler.function.__annotations__.items() if k not in {"self", "return"}
        }

        # remove any **extra keys/values which aren't expected by the handler function
        for extra_k in list(extra.keys()):
            if extra_k not in annos:
                del extra[extra_k]

        handler_args = list[Any]()
        handler_kwargs = dict[str, Any]()

        if isinstance(packet.data, dict):
            handler_kwargs = packet.data
        elif packet.data is None:
            # check if None is an expected value for an argument rather than signifying there's
            # no data passed
            if len(annos) != 0:
                handler_args.append(None)
        else:
            handler_args.append(packet.data)

        self.logger.debug(
            "Calling packet handler %s with args %s and kwargs %s",
            handler.function.__qualname__,
            handler_args,
            handler_kwargs,
        )

        try:
            response = await validate_arguments(handler.function)(
                *handler_args,
                **handler_kwargs,
                **extra,
            )
        except ValidationError:
            self.logger.info(
                (
                    "A ValidationError ocurred while calling the packet handler %s with args %s "
                    "and kwargs %s"
                ),
                handler.function.__qualname__,
                handler_args,
                handler_kwargs,
            )
            raise

        if not isinstance(response, PACKET_DATA_TYPES):
            raise TypeError(
                f"Packet handler {handler.function.__qualname__} returned an unsupported type: "
                f"'{type(response).__name__}'",
            )

        self.logger.debug(
            "Received value %s from packet handler %s",
            response,
            handler.function.__qualname__,
        )

        return response
