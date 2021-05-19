from discord.ext import commands
import aiohttp
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from util.setup import villager_bot_intents, setup_logging, setup_database


class VillagerBotShard:
    def __init__(self, shard_count: int, shard_id: int):
        self.shard_count = shard_count
        self.shard_id = shard_id

        self.aiohttp = aiohttp.ClientSession()
        self.logger = setup_logging()
        self.db = setup_database()

        self.bot = commands.Bot(
            shard_count=shard_count,
            shard_id=shard_id,
            prefix=self.get_prefix,
            intents=villager_bot_intents(),
        )

        self.ipc_port = 42069 + shard_id
