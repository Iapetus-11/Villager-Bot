from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class CommandCooldownsResource(KarenResourceBase):
    async def get_or_create(self, user_id: str | int, command: str):
        await self._http.post(url_join())
