from pydantic import BaseModel, Extra

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

    class Config:
        validate_all = True
        allow_mutation = False
        extra = Extra.forbid
