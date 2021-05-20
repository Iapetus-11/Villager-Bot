from concurrent.futures import ProcessPoolExecutor
from classyjson import ClassyDict
import aiofiles
import asyncio
import logging

from util.setup import load_secrets, load_data, setup_karen_logging
from util.ipc import Server, Stream
from bot import run_shard


class MechaKaren:
    def __init__(self):
        self.k = load_secrets()
        self.d = load_data()

        self.logger = setup_karen_logging()
        self.server = Server(self.k.manager.host, self.k.manager.port, self.k.manager.auth, self.handle_packet)

        self.shard_ids = tuple(range(self.d.shard_count))
        self.online_shards = set()

    async def handle_packet(self, stream: Stream, packet: ClassyDict):
        if packet.type == "shard-ready":
            self.online_shards.add(packet.shard_id)

            if len(self.online_shards) == len(self.shard_ids):
                self.logger.info(f"\u001b[36;1mALL SHARDS\u001b[0m [0-{len(self.online_shards)}] \u001b[36;1mREADY\u001b[0m")
        elif packet.type == "shard-disconnect":
            self.online_shards.discard(packet.shard_id)
        elif packet.type == "broadcast":
            await asyncio.gather(*[stream.send_packet(packet.packet) for stream in self.server.connections])

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
