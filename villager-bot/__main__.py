from concurrent.futures import ProcessPoolExecutor, wait
from classyjson import ClassyDict
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from util.ipc import Server, Stream
from bot import run_shard


async def handle_packet(shard_id: int, stream: Stream, packet: ClassyDict) -> None:
    print(f"packet from {shard_id}:", packet)


async def main(ppool):
    loop = asyncio.get_event_loop()

    ipc_server = Server("0.0.0.0", 42069, "auth123")

    shard_count = 5
    coros = [loop.run_in_executor(ppool, run_shard, ...) for shard_id in range(shard_count)]

    await asyncio.gather(*coros)


if __name__ == "__main__":
    with ProcessPoolExecutor() as ppool:
        asyncio.run(main(ppool))
