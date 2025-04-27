from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase


class User(ImmutableBaseModel):
    pass


class KarenUsers(KarenResourceBase):
    async def get(id_: str | None = None, *, discord_id: int | None = None):
        if id_ is not None and discord_id is not None:
            raise ValueError("You cannot provide both ID params at once")

        if id_ is None and discord_id is None:
            raise ValueError("You must provide at least one ID param")
