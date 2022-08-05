from pydantic import BaseModel

from common.models.secrets import DatabaseSecrets, KarenSecrets


class Secrets(BaseModel):
    default_prefix: str
    discord_token: str
    karen: KarenSecrets
    database: DatabaseSecrets
    google_search: list[str]
    xapi_key: str
    rcon_fernet_key: str
