from typing import Any, TypedDict, Unpack, overload
from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.utils import MISSING_SENTINEL
from bot.utils.urls import url_join

from ...client import KarenResourceBase


class DiscordGuildSettings(ImmutableBaseModel):
    id: int
    prefix: str
    language: str
    mc_server: str | None
    silly_triggers: bool
    disabled_commands: set[str]


class DiscordGuildUpdateRequest(TypedDict):
    prefix: str
    language: str
    mc_server: str | None
    silly_triggers: bool
    disabled_commands: set[str]


class DiscordGuildsResource(KarenResourceBase):
    UPDATEABLE_FIELDS = set(DiscordGuildUpdateRequest.__annotations__.keys())

    async def get(self, id_: int) -> DiscordGuildSettings:
        response = await self._http.get(url_join("guilds", id_), allow_redirects=False)
        data = await response.read()

        return DiscordGuildSettings.model_validate_json(data)

    @overload
    async def update(self, id_: int, discord_guild_settings: DiscordGuildSettings, /):
        ...

    @overload
    async def update(self, id_: int, /, **kwargs: Unpack[DiscordGuildUpdateRequest]):
        ...

    async def update(self, id_: int, /, *args, **kwargs):
        payload: dict[str, Any]
        if isinstance(discord_guild_settings := next(iter(args), None), DiscordGuildSettings):
            payload = discord_guild_settings.model_dump(include=self.UPDATEABLE_FIELDS)
        else:
            payload = kwargs

        response = await self._http.patch(url_join("guilds", id_), json=payload)
        data = await response.read()

        return DiscordGuildSettings.model_validate_json(data)
