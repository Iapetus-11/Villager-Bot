from pydantic import BaseModel

from common.models.secrets import DatabaseSecrets, KarenSecrets


class TopggWebhookSecrets(BaseModel):
    host: str
    port: int
    path: str
    auth: str


class Secrets(BaseModel):
    cluster_count: int
    shard_count: int
    karen: KarenSecrets
    topgg_webhook: TopggWebhookSecrets
    database: DatabaseSecrets
