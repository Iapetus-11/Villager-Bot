from concurrent.futures import ProcessPoolExecutor
from classyjson import ClassyDict
import aiofiles
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from util.ipc import Server, Stream
from util.setup import load_text, load_secrets, load_data
from bot import run_shard


async def handle_packet(shard_id: int, stream: Stream, packet: ClassyDict) -> None:
    print(f"MANAGER: packet from {shard_id}:", packet)


def main(ppool):
    secrets, data = load_secrets(), load_data()

    manager_server = Server(secrets.manager.host, secrets.manager.port, secrets.manager.auth, handle_packet)

    async def _main():
        await manager_server.start()

        shards = []
        loop = asyncio.get_event_loop()

        for shard_id in range(data.shard_count):
            shards.append(loop.run_in_executor(ppool, run_shard, data.shard_count, shard_id))

        await asyncio.gather(*shards)

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    with ProcessPoolExecutor() as ppool:
        main(ppool)
