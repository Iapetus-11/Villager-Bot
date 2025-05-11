from __future__ import annotations

from datetime import timedelta

import aiohttp

from bot.services.karen.cache import KarenResourceCache
from bot.services.karen.client import KarenResourceBase


class DiscordResourceGroup(KarenResourceBase):
    class Cached:
        def __init__(self, discord: DiscordResourceGroup):
            self.guilds = KarenResourceCache(discord.guilds, expire_after=timedelta(hours=1))

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        BASE_PATH = "/discord/"

        from .guild import DiscordGuildsResource

        self.guilds = DiscordGuildsResource(http, base_path=BASE_PATH)

        self.cached = self.Cached(self)
