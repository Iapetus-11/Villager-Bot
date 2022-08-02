from typing import Optional, TypeAlias
from pydantic import BaseModel

from common.coms.packet_type import PacketType
from common.coms.json_encoder import loads, dumps


VALID_PACKET_DATA_TYPES: TypeAlias = str | int | float | dict | list | set | None


class Packet(BaseModel):
    id: str
    type: Optional[PacketType] = None
    data: dict[str, VALID_PACKET_DATA_TYPES]

    class Config:
        json_loads = loads
        json_dumps = dumps
