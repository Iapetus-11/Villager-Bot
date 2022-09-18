from pydantic import Field

from common.models.base import ImmutableBaseModel
from common.models.logging_config import LoggingConfig
from common.models.secrets import KarenSecrets


class TopggWebhookSecrets(ImmutableBaseModel):
    host: str
    port: int
    path: str
    auth: str


class DatabaseSecrets(ImmutableBaseModel):
    host: str
    port: int = Field(gt=0, le=65535)
    name: str
    user: str
    auth: str
    pool_size: int = Field(ge=1)


class Secrets(ImmutableBaseModel):
    cluster_count: int
    shard_count: int
    bot_id: int
    karen: KarenSecrets
    topgg_api: str
    topgg_webhook: TopggWebhookSecrets
    database: DatabaseSecrets
    logging: LoggingConfig
