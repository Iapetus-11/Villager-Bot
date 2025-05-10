import aiohttp

from bot.services.karen.client import KarenResourceBase


class GameResourceGroup(KarenResourceBase):

    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        BASE_PATH = "/game/"

        from .command_cooldowns import CommandCooldownsResource
        self.command_cooldowns = CommandCooldownsResource(http, base_path=BASE_PATH)
