import aiohttp

from bot.services.karen.client import KarenResourceBase


class GameResourceGroup(KarenResourceBase):
    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        from .command_cooldowns import CommandCooldownsResource
        from .commands import CommandsResourceGroup

        self.command_cooldowns = CommandCooldownsResource(http)
        self.commands = CommandsResourceGroup(http)
