from __future__ import annotations

import abc
from datetime import timedelta

import aiohttp

from bot.utils.urls import url_join

from .cache import KarenResourceCache


def _patch_client_session(client_session: aiohttp.ClientSession, base_path: str | None):
    """A very dirty hack to allow me to organize nested resources with nested routes in a nice way"""

    if not base_path:
        return

    import http

    def method_wrapper(client_session_method):
        def method_caller(url: str, *args, **kwargs):
            client_session_method(url_join(base_path, url), *args, **kwargs)

        return method_caller

    for http_method in map(str.lower, http.HTTPMethod):
        setattr(client_session, http_method, method_wrapper(getattr(client_session, http_method)))


class KarenResourceBase(abc.ABC):
    def __init__(self, http: aiohttp.ClientSession, *, base_path: str | None = None):
        self._http = http
        _patch_client_session(http, base_path)

        self._base_path = base_path


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
            headers={"Authorization": f"Token {api_key}"},
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
