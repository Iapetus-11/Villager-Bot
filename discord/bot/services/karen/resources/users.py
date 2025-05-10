from datetime import datetime

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase


class User(ImmutableBaseModel):
    id: str
    discord_id: int | None
    banned: bool
    emeralds: int
    vault_balance: int
    vault_max: int
    health: int
    vote_streak: int
    last_vote_at: datetime | None
    give_alert: bool
    shield_pearl_activated_at: datetime | None
    last_daily_quest_reroll: datetime
    modified_at: datetime


class UsersResource(KarenResourceBase):
    async def get(self, id_: str | int) -> User:
        response = await self._http.get(f"/users/{id_}/", allow_redirects=False)
        data = await response.read()

        return User.model_validate_json(data)
