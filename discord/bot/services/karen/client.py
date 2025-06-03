from __future__ import annotations

import abc
import logging
from datetime import timedelta

import aiohttp

from bot.services.karen.errors import KarenGameError, KarenResponseError

from .cache import KarenResourceCache

logger = logging.getLogger(__name__)


class KarenResourceBase(abc.ABC):
    def __init__(self, http: aiohttp.ClientSession):
        self._http = http


async def raise_for_status(resp: aiohttp.ClientResponse):
    if error := await KarenResponseError.from_response(resp):
        KarenGameError.raise_from_response_error(error)


class KarenClient:
    class Cached:
        def __init__(self, karen: KarenClient):
            self.users = KarenResourceCache(karen.users, expire_after=timedelta(hours=1))

    def __init__(self, base_url: str, api_key: str):
        self._http = aiohttp.ClientSession(
            conn_timeout=1.0,
            read_timeout=30.0,
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            raise_for_status=raise_for_status,
        )

        from .resources.command_executions import CommandExecutionsResource
        from .resources.commands import CommandsResourceGroup
        from .resources.discord import DiscordResourceGroup
        from .resources.users import UsersResourceGroup

        self.command_executions = CommandExecutionsResource(self._http)
        self.commands = CommandsResourceGroup(self._http)
        self.discord = DiscordResourceGroup(self._http)
        self.users = UsersResourceGroup(self._http)

        self.cached = self.Cached(self)

    async def close(self):
        await self._http.close()
