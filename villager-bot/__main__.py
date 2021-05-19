from concurrent.futures import ProcessPoolExecutor
from classyjson import ClassyDict
import aiofiles
import asyncio
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from util.ipc import Server, Stream
from util.setup import load_text, load_secrets, load_data
from bot import run_shard


class Karen:
    def __init__(self):
        self.k = load_secrets()
        self.d = load_data()

        self.server = Server(self.k.manager.host, self.k.manager.port, self.k.manager.auth, self.handle_packet)

    async def handle_packet(self, *args):
        print(args)

    async def start(self, pp):
        await self.server.start()

        shards = []
        loop = asyncio.get_event_loop()

        for shard_id in range(self.d.shard_count):
            shards.append(loop.run_in_executor(pp, run_shard, self.d.shard_count, shard_id))

        await asyncio.gather(*shards)

    def run(self):
        with ProcessPoolExecutor(self.d.shard_count) as pp:
            asyncio.run(self.start(pp))


if __name__ == "__main__":
    karen = Karen()

    try:
        karen.run()
    except KeyboardInterrupt:
        pass
