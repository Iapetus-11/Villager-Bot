from typing import Optional
from pydantic import BaseModel


class Guild(BaseModel):
    guild_id: int
    prefix: str
    difficulty: str
    language: str
    mc_server: Optional[str]
    do_replies: bool
