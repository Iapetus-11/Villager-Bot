from datetime import datetime
from time import timezone

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase


class CooldownCheck(ImmutableBaseModel):
    already_on_cooldown: bool
    until: datetime


class CommandCooldownsResource(KarenResourceBase):
    async def check(self, user_id: str, command: str) -> CooldownCheck:
        response = await self._http.post(
            "/cooldowns/check/",
            json={
                "user_id": user_id,
                "command": command,
                "from": datetime.now(timezone.utc).isoformat(),
            },
            allow_redirects=False,
        )
        data = await response.read()

        return CooldownCheck.model_validate_json(data)
