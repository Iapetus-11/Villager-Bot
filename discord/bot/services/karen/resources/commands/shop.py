from typing import ClassVar

from pydantic import RootModel

from bot.models.base_model import ImmutableBaseModel
from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class ShopItemEntryRequires(ImmutableBaseModel):
    count_lt: int | None
    items: dict[str, int] | None


class ShopItemEntry(ImmutableBaseModel):
    buy_price: int
    requires: ShopItemEntryRequires | None


class ShopCommandResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/commands/shop/"

    async def get_items_for_category(self, category: str) -> dict[str, ShopItemEntry]:
        response = await self._http.get(url_join(self.BASE_URL, "items", category))
        data = await response.read()

        return RootModel[dict[str, ShopItemEntry]].model_validate_json(data).root
