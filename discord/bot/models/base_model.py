from functools import cached_property

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    model_config: ConfigDict = ConfigDict(validate_default=True, ignored_types=(cached_property,))

    def __getitem__(self, key: str):
        return getattr(self, key)


class ImmutableBaseModel(BaseModel):
    model_config: ConfigDict = {**BaseModel.model_config, **ConfigDict(frozen=True)}
