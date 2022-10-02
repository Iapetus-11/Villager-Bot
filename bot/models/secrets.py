from common.models.base_model import ImmutableBaseModel
from common.models.logging_config import LoggingConfig
from common.models.secrets import KarenSecrets


class Secrets(ImmutableBaseModel):
    default_prefix: str
    discord_token: str
    support_server_id: int
    error_channel_id: int
    vote_channel_id: int
    dm_logs_channel_id: int
    karen: KarenSecrets
    google_search: list[str]
    xapi_key: str
    rcon_fernet_key: str
    logging: LoggingConfig
