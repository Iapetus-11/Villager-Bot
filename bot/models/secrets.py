from common.models.base import ImmutableBaseModel
from common.models.secrets import KarenSecrets


class Secrets(ImmutableBaseModel):
    default_prefix: str
    discord_token: str
    karen: KarenSecrets
    google_search: list[str]
    xapi_key: str
    rcon_fernet_key: str
