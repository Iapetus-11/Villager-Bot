from typing import Optional, TypeAlias

from pydantic import BaseModel

from common.coms.json_encoder import dumps, loads
from common.coms.packet_type import PacketType

T_PACKET_DATA: TypeAlias = str | int | float | dict | list | set | None | BaseModel


class Packet(BaseModel):
    id: str
    type: Optional[PacketType] = None
    data: dict[str, T_PACKET_DATA]
    error: bool

    class Config:
        json_loads = loads
        json_dumps = dumps
        mutable = False
