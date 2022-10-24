from datetime import datetime, timedelta
from typing import Any, Optional, TypeAlias

import arrow
from pydantic import BaseModel

from common.coms.packet_type import PacketType

# order matters in this due to the way Pydantic handles parsing
T_PACKET_DATA: TypeAlias = (
    bool
    | int
    | float
    | datetime
    | timedelta
    | arrow.Arrow
    | set[Any]
    | list[Any]
    | dict[str, Any]
    | None
    | BaseModel
    | str
)

PACKET_DATA_TYPES = (
    bool,
    int,
    float,
    datetime,
    timedelta,
    arrow.Arrow,
    set,
    list,
    dict,
    type(None),
    BaseModel,
    str,
)


class Packet(BaseModel):
    id: str
    type: Optional[PacketType] = None
    data: T_PACKET_DATA
    error: bool = False

    class Config:
        allow_mutation = False
        smart_union = True
        arbitrary_types_allowed = True
