from bot.models.base_model import ImmutableBaseModel
from ...client import KarenResourceBase


class DiscordGuildSettings(ImmutableBaseModel):
    id: int
    prefix: str
    language: str
    mc_server: str | None
    silly_triggers: bool


class DiscordGuildsResource(KarenResourceBase):
    async def get(self, id_: int) -> DiscordGuildSettings:
        response = await self._http.get(f"/discord/guilds/{id_}/", allow_redirects=False)
        data = await response.read()

        return DiscordGuildSettings.model_validate_json(data)
