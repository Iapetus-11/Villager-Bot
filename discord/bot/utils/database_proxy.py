from typing import Any

from bot.utils.karen_client import KarenClient


class DatabaseProxy:
    """Provides an API similar to that of an asyncpg.Pool but proxies calls through Karen"""

    __slots__ = ("karen",)

    def __init__(self, karen: KarenClient):
        self.karen = karen

    async def execute(self, query: str, *args: Any) -> None:
        await self.karen.db_exec(query, *args)

    async def executemany(self, query: str, args: list[list[Any]]) -> None:
        await self.karen.db_exec_many(query, args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        return await self.karen.db_fetch_val(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        return await self.karen.db_fetch_row(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        return await self.karen.db_fetch_all(query, *args)
