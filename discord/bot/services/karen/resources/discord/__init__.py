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

        from .guild import DiscordGuildsResource

        self.guilds = DiscordGuildsResource(http)

        self.cached = self.Cached(self)
