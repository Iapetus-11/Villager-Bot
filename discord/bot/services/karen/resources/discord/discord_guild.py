
from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase


class DiscordGuild(ImmutableBaseModel):
    id: int
    prefix: str
    language: str
    mc_server: str | None
    silly_triggers: bool


class DiscordGuildsResource(KarenResourceBase):
    async def get(self, id_: int) -> DiscordGuild:
        response = await self._http.get(f"/discord/guilds/{id_}/", allow_redirects=False)
        data = await response.read()

        return DiscordGuild.model_validate_json(data)
