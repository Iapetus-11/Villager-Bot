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
    async def get(self, id_: str | None = None, *, discord_id: int | None = None) -> User:
        if id_ is not None and discord_id is not None:
            raise ValueError("You cannot provide both ID params at once")

        if id_ is None and discord_id is None:
            raise ValueError("You must provide at least one ID param")

        response = await self._http.get(f"/users/{id_ or discord_id}/", allow_redirects=False)
        data = await response.read()

        return User.model_validate_json(data)
