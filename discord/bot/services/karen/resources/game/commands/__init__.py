from typing import ClassVar

import aiohttp

from bot.services.karen.client import KarenResourceBase
from bot.services.karen.resources.game.commands.profile import ProfileCommandResource


class CommandsResourceGroup(KarenResourceBase):
    BASE_URL: ClassVar[str] = "/game/commands/"

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        self.profile = ProfileCommandResource(http)
