from __future__ import annotations

import abc
from datetime import timedelta

import aiohttp

from .cache import KarenResourceCache


class KarenResourceBase(abc.ABC):
    def __init__(self, http: aiohttp.ClientSession):
        self._http = http


class KarenClient:
    class Cached:
        def __init__(self, karen: KarenClient):
            self.users = KarenResourceCache(karen.users, expire_after=timedelta(hours=1))

    def __init__(self, base_url: str, api_key: str):
        self._http = aiohttp.ClientSession(
            raise_for_status=True,
            conn_timeout=1.0,
            read_timeout=30.0,
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

        from .resources.discord import DiscordResourceGroup
        from .resources.game import GameResourceGroup
        from .resources.users import UsersResourceGroup

        self.discord = DiscordResourceGroup(self._http)
        self.game = GameResourceGroup(self._http)
        self.users = UsersResourceGroup(self._http)

        self.cached = self.Cached(self)

    async def close(self):
        await self._http.close()
