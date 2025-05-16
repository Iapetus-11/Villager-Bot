from datetime import datetime, timezone
from typing import ClassVar

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class CooldownCheck(ImmutableBaseModel):
    already_on_cooldown: bool
    until: datetime


class CommandCooldownsResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/game/cooldowns/"

    async def check(self, user_id: str, command: str) -> CooldownCheck:
        response = await self._http.post(
            url_join(self.BASE_URL, "/check/"),
            json={
                "user_id": user_id,
                "command": command,
                "from": datetime.now(timezone.utc).isoformat(),
            },
            allow_redirects=False,
        )
        data = await response.read()

        return CooldownCheck.model_validate_json(data)
