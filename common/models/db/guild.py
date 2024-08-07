from pydantic import BaseModel


class Guild(BaseModel):
    guild_id: int
    prefix: str
    language: str
    mc_server: str | None
    do_replies: bool
