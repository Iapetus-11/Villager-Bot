from typing import Any, Optional, TypeAlias

from pydantic import BaseModel

from common.coms.json_encoder import dumps, loads
from common.coms.packet_type import PacketType

T_PACKET_DATA: TypeAlias = (
    bool | str | int | float | set[Any] | list[Any] | dict[str, Any] | None | BaseModel
)

PACKET_DATA_TYPES = (bool, str, int, float, set, list, dict, type(None), BaseModel)


class Packet(BaseModel):
    id: str
    type: Optional[PacketType] = None
    data: T_PACKET_DATA
    error: bool = False

    class Config:
        json_loads = loads
        json_dumps = dumps
        allow_mutation = False
        smart_union = True
