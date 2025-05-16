from functools import cached_property
from typing import ClassVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(validate_default=True, ignored_types=(cached_property,))

    def __getitem__(self, key: str):
        return getattr(self, key)


class ImmutableBaseModel(BaseModel):
    model_config: ClassVar[ConfigDict] = {**BaseModel.model_config, **ConfigDict(frozen=True)}
