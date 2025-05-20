from datetime import datetime
from typing import ClassVar

import aiohttp

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class ProfileCommandData(ImmutableBaseModel):
    net_wealth: int
    mooderalds: int
    vote_streak: int
    can_vote: bool
    next_vote_time: datetime | None
    pickaxe: str
    sword: str
    hoe: str
    active_effects: set[str]


class ProfileCommandResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/commands/profile/"

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

    async def get(self, user_id: str | int) -> ProfileCommandData:
        response = await self._http.get(url_join(self.BASE_URL, user_id), allow_redirects=False)
        data = await response.read()

        return ProfileCommandData.model_validate_json(data)
