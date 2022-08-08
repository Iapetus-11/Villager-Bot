from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    class Config:
        validate_all = True
        # extra = Extra.forbid


class ImmutableBaseModel(PydanticBaseModel):
    class Config:
        validate_all = True
        # extra = Extra.forbid
        allow_mutation = False
