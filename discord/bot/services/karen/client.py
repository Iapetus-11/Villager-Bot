from __future__ import annotations

import abc
import logging
from datetime import timedelta
from http import HTTPStatus

import aiohttp

from .cache import KarenResourceCache

logger = logging.getLogger(__name__)


class KarenResourceBase(abc.ABC):
    def __init__(self, http: aiohttp.ClientSession):
        self._http = http


async def raise_for_status(resp: aiohttp.ClientResponse):
    if not HTTPStatus(resp.status).is_success:
        try:
            response_content = await resp.read()  # Connection closed at this point :/
        except Exception:
            response_content = None

    try:
        resp.raise_for_status()
    except aiohttp.ClientResponseError:
        logger.exception(
            f"Request {resp.request_info.method} {str(resp.url).removeprefix(resp.url.host or '')} "
            f"failed ({resp.status}): {response_content!s}"
        )

        raise


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
