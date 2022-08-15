from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    class Config:
        validate_all = True

    def __getitem__(self, key: str):
        return getattr(self, key)


class ImmutableBaseModel(BaseModel):
    class Config:
        allow_mutation = False
