from datetime import datetime
from typing import ClassVar, TypedDict, Unpack

from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class LogCommandExecutionRequest(TypedDict):
    guild_id: int
    command: str
    at: datetime
    user_id: str | int


class CommandExecutionsResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/game/command_executions/"

    async def log(self, **kwargs: Unpack[LogCommandExecutionRequest]) -> None:
        await self._http.post(
            url_join(self.BASE_URL, "/log/"),
            json=kwargs,
            allow_redirects=False,
        )
