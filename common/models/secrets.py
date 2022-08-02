from pydantic import BaseModel, Field


class KarenSecrets(BaseModel):
    host: str
    port: int
    auth: str


class DatabaseSecrets(BaseModel):
    host: str
    port: int
    name: str
    user: str
    auth: str
    pool_size: int = Field(ge=1)
