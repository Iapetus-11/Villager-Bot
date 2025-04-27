from bot.models.base_model import ImmutableBaseModel
from bot.models.logging_config import LoggingConfig


class Secrets(ImmutableBaseModel):
    default_prefix: str
    discord_token: str
    owner_id: int
    support_server_id: int
    error_channel_id: int
    vote_channel_id: int
    dm_logs_channel_id: int
    google_search: list[str]
    xapi_key: str
    rcon_fernet_key: str
    deepl_api_key: str
    logging: LoggingConfig
