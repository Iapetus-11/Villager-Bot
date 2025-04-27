import datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: int
    bot_banned: bool = Field(default=False)
    emeralds: int = Field(default=0)
    vault_balance: int = Field(default=0)
    vault_max: int = Field(default=1)
    health: int = Field(default=20)
    vote_streak: int = Field(default=0)
    last_vote: datetime.datetime | None
    give_alert: bool = Field(default=True)
    shield_pearl: datetime.datetime | None
    last_dq_reroll: datetime.datetime
