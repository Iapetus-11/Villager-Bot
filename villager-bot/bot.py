from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.ipc import Client


class VillagerBotShard:
    def __init__(self, shard_count: int, shard_id: int, secrets: ClassyDict, data: ClassyDict, text: ClassyDict) -> None:
        self.shard_count = shard_count
        self.shard_id = shard_id

        self.k = secrets
        self.d = data
        self.l = text

        self.aiohttp = aiohttp.ClientSession()
        self.logger = setup_logging(shard_id)
        self.db = setup_database(secrets)

        self.bot = commands.Bot(
            shard_count=shard_count,
            shard_id=shard_id,
            prefix=self.get_prefix,
            intents=villager_bot_intents(),
        )

        self.ipc = Client(
            secrets.manager.host, # ip manager is hosted on
            secrets.manager.port, # port manager is hosted on
            secrets.manager.auth, # auth which is passed with every packet
        )

    async def setup(self):
        await self.ipc.connect(self.shard_id)  # connect to manager server
        await self.db  # connect to database
