from datetime import datetime

import aiohttp

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase


class ProfileCommandData(ImmutableBaseModel):
    net_wealth: int
    mooderalds: int
    vote_streak: int
    can_vote: bool
    next_vote_time: datetime | None
    pickaxe: str
    sword: str
    hoe: str
    active_effects: list[str]


class CommandsResourceGroup(KarenResourceBase):
    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http, base_path="/commands/")

    async def get_profile_data(self, user_id: str | int) -> ProfileCommandData:
        response = await self._http.get(f"/profile/{user_id}/", allow_redirects=False)
        data = await response.read()

        return ProfileCommandData.model_validate_json(data)
