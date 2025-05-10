from typing import Annotated

from pydantic import Field

from bot.models.base_model import ImmutableBaseModel


class LoggingOverride(ImmutableBaseModel):
    level: str


class LoggingConfig(ImmutableBaseModel):
    level: str
    overrides: Annotated[dict[str, LoggingOverride], Field(default_factory=dict)]
