from datetime import datetime
from typing import Annotated, Any, ClassVar, Literal, TypedDict, Unpack

from pydantic import Discriminator, RootModel, Tag

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class CommandExecutionPreflightRequest(TypedDict):
    user_id: str | int
    command: str
    at: datetime
    discord_guild_id: int | None


class CommandExecutionPreflightSuccess(ImmutableBaseModel):
    spawn_mob: bool


class CommandExecutionPreflightCommandOnCooldownError(ImmutableBaseModel):
    error_type: Literal["CommandOnCooldown"]
    until: datetime


def _get_command_execution_preflight_discriminator(v: Any) -> str | None:
    if isinstance(v, dict):
        if "error_type" in v:
            return v["error_type"]

        return "Success"

    return None


CommandExecutionPreflightResponse = RootModel[
    Annotated[
        (
            Annotated[CommandExecutionPreflightSuccess, Tag("Success")]
            | Annotated[CommandExecutionPreflightCommandOnCooldownError, Tag("CommandOnCooldown")]
        ),
        Discriminator(_get_command_execution_preflight_discriminator),
    ]
]


class CommandExecutionsResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/command_executions/"

    async def preflight(self, **kwargs: Unpack[CommandExecutionPreflightRequest]) -> CommandExecutionPreflightResponse:
        response = await self._http.post(
            url_join(self.BASE_URL, "/preflight/"),
            json=kwargs,
            allow_redirects=False,
        )
        data = await response.read()

        return CommandExecutionPreflightResponse.model_validate_json(data)
