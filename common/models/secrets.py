from pydantic import BaseModel, Field


class KarenSecrets(BaseModel):
    host: str
    port: int = Field(gt=0, le=65535)
    auth: str


class DatabaseSecrets(BaseModel):
    host: str
    port: int = Field(gt=0, le=65535)
    name: str
    user: str
    auth: str
    pool_size: int = Field(ge=1)
