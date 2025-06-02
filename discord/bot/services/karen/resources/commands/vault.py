from typing import ClassVar, Literal

import aiohttp

from bot.services.karen.client import KarenResourceBase
from bot.utils.urls import url_join


class VaultCommandResource(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/commands/vault/"

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

    async def deposit(self, user_id: str, *, blocks: int | Literal["Max"]) -> None:
        await self._http.post(
            url_join(self.BASE_URL, user_id, "deposit"),
            json={
                "blocks": blocks,
            },
            allow_redirects=False,
        )

    async def withdraw(self, user_id: str, *, blocks: int | Literal["Max"]) -> None:
        await self._http.post(
            url_join(self.BASE_URL, user_id, "withdraw"),
            json={
                "blocks": blocks,
            },
            allow_redirects=False,
        )
