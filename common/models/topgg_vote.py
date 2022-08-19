from typing import Optional
from common.models.base import BaseModel

class TopggVote(BaseModel):
    bot: int
    user: int
    type: str
    isWeekend: bool
    query: Optional[str]
