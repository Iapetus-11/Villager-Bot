from concurrent.futures import ThreadPoolExecutor, wait
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


async def main(ppool):
    shard_args = await asyncio.gather(load_secrets(), load_data(), load_text())
    secrets, data, text = shard_args

    ipc_server = Server(secrets.manager.host, secrets.manager.port, secrets.manager.auth, handle_packet)
    await ipc_server.start()

    loop = asyncio.get_event_loop()
    coros = [loop.run_in_executor(ppool, run_shard, data.shard_count, shard_id, *shard_args) for shard_id in range(data.shard_count)]

    await asyncio.gather(*coros)


if __name__ == "__main__":
    with ThreadPoolExecutor() as ppool:
        asyncio.run(main(ppool))
