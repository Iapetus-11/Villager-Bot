import aiohttp

from bot.services.karen.client import KarenResourceBase


class GameResourceGroup(KarenResourceBase):
    def __init__(self, http: aiohttp.ClientSession):
        super().__init__(http)

        from .command_cooldowns import CommandCooldownsResource
        from .command_executions import CommandExecutionsResource
        from .commands import CommandsResourceGroup

        self.command_cooldowns = CommandCooldownsResource(http)
        self.command_executions = CommandExecutionsResource(http)
        self.commands = CommandsResourceGroup(http)
