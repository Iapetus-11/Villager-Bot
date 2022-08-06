import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

import numpy
import pyximport

from common.coms.client import Client
from common.utils.setup import load_data

from bot.utils.setup import load_secrets, load_translations, setup_logging
from bot.villager_bot import VillagerBotCluster


async def main_async(tp: ThreadPoolExecutor):
    cluster_id = os.getpid()

    secrets = load_secrets()
    translations = load_translations()
    data = load_data()

    villager_bot = VillagerBotCluster(cluster_id, tp, secrets, data, translations)

    async with villager_bot:
        await villager_bot.start()


def main():
    # add cython support, with numpy header files
    pyximport.install(language_level=3, setup_args={"include_dirs": numpy.get_include()})

    with ThreadPoolExecutor() as tp:
        asyncio.run(main_async(tp))


if __name__ == "__main__":
    main()
