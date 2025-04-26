from bot.models.base_model import ImmutableBaseModel


class ForwardedDirectMessage(ImmutableBaseModel):
    user_id: int
    channel_id: int
    message_id: int
    content: str
