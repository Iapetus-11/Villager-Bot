from concurrent.futures import ProcessPoolExecutor
from classyjson import ClassyDict
import aiofiles
import asyncio
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from util.setup import load_text, load_secrets, load_data, setup_karen_logging
from util.ipc import Server, Stream
from bot import run_shard


class Karen:
    def __init__(self):
        self.k = load_secrets()
        self.d = load_data()

        self.logger = setup_karen_logging()
        self.server = Server(self.k.manager.host, self.k.manager.port, self.k.manager.auth, self.handle_packet)

        self.shard_ids = tuple(range(self.d.shard_count))

        self.ready_shards = set()

    async def handle_packet(self, stream: Stream, packet: ClassyDict):
        if packet.type == "ready-event":
            self.ready_shards.add(packet.shard_id)

            if len(self.ready_shards) == len(self.shard_ids):
                self.logger.info("\u001b[36;1mALL SHARDS READY\u001b[0m")

    async def start(self, pp):
        await self.server.start()

        shard_groups = []
        loop = asyncio.get_event_loop()

        for shard_id_group in [self.shard_ids[i : i + 4] for i in range(0, len(self.shard_ids), 4)]:
            shard_groups.append(loop.run_in_executor(pp, run_shard, self.d.shard_count, shard_id_group))

        await asyncio.gather(*shard_groups)

    def run(self):
        with ProcessPoolExecutor(self.d.shard_count) as pp:
            asyncio.run(self.start(pp))


if __name__ == "__main__":
    karen = Karen()

    try:
        karen.run()
    except KeyboardInterrupt:
        pass
