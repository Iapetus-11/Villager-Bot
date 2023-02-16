from functools import cached_property

from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    class Config:
        validate_all = True
        keep_untouched = (cached_property,)

    def __getitem__(self, key: str):
        return getattr(self, key)


class ImmutableBaseModel(BaseModel):
    class Config:
        allow_mutation = False
