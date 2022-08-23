from common.models.base import ImmutableBaseModel


class ForwardedDirectMessage(ImmutableBaseModel):
    user_id: int
    channel_id: int
    message_id: int
    content: str
