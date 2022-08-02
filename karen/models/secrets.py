from pydantic import BaseModel

from common.models.secrets import DatabaseSecrets, KarenSecrets


class TopggWebhookSecrets(BaseModel):
    host: str
    port: int
    path: str
    auth: str


class Secrets(BaseModel):
    karen: KarenSecrets
    topgg_webhook: TopggWebhookSecrets
    database: DatabaseSecrets
