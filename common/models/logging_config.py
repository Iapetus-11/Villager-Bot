from pydantic import Field

from common.models.base_model import ImmutableBaseModel


class LoggingOverride(ImmutableBaseModel):
    level: str


class LoggingConfig(ImmutableBaseModel):
    level: str
    overrides: dict[str, LoggingOverride] = Field(default_factory=dict)
