from typing import Any, Optional, TypeAlias

from pydantic import BaseModel

from common.coms.json_encoder import dumps, loads
from common.coms.packet_type import PacketType

T_PACKET_DATA: TypeAlias = (
    str | int | float | dict[str, Any] | list[Any] | set[Any] | None | BaseModel
)

PACKET_DATA_TYPES = (str, int, float, dict, list, set, type(None), BaseModel)


class Packet(BaseModel):
    id: str
    type: Optional[PacketType] = None
    data: T_PACKET_DATA
    error: bool = False

    class Config:
        json_loads = loads
        json_dumps = dumps
        allow_mutation = False
