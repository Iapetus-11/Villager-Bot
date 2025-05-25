from pydantic import RootModel

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase


class Item(ImmutableBaseModel):
    name: str
    sell_price: int
    amount: int
    sticky: bool
    sellable: bool


class ItemsResource(KarenResourceBase):
    BASE_PATH = "/users/{user_id}/items/"

    async def list(self, user_id: str, *, category: str | None = None) -> list[Item]:
        response = await self._http.get(
            self.BASE_PATH.format(user_id=user_id), params={**({} if category is None else {"category": category})}
        )
        data = await response.read()

        return RootModel[list[Item]].model_validate_json(data).root
