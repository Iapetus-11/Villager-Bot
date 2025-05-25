from datetime import datetime
from typing import ClassVar

import aiohttp

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


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
    last_daily_quest_reroll: datetime | None
    modified_at: datetime


class UsersResourceGroup(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/users/"

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        from .badges import BadgesResource
        from .items import ItemsResource

        self.badges = BadgesResource(http)
        self.items = ItemsResource(http)

    async def get(self, id_: str | int) -> User:
        response = await self._http.get(url_join(self.BASE_URL, f"/{id_}/"), allow_redirects=False)
        data = await response.read()

        return User.model_validate_json(data)
