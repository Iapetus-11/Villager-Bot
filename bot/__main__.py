import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import signal
import sys

from common.utils.setup import load_data

from bot.utils.setup import load_secrets, load_translations
from bot.utils.add_cython_ext import add_cython_ext
from bot.villager_bot import VillagerBotCluster

if not vars(sys.modules[__name__])['__package__']:
    print("Villager Bot must be ran as a module (using the -m flag)")
    sys.exit(1)

async def main_async(tp: ThreadPoolExecutor) -> None:
    secrets = load_secrets()
    translations = load_translations()
    data = load_data()

    villager_bot = VillagerBotCluster(tp, secrets, data, translations)

    async with villager_bot:
        if os.name != "nt":
            # register sigterm handler
            asyncio.get_event_loop().add_signal_handler(
                signal.SIGTERM, lambda: asyncio.create_task(villager_bot.close())
            )

        await villager_bot.start()


def main(args: list[str]) -> None:
    add_cython_ext()

    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    if "--build-pyx-only" not in args:
        with ThreadPoolExecutor() as tp:
            asyncio.run(main_async(tp))


if __name__ == "__main__":
    main(sys.argv[1:])
