import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import signal

from common.utils.setup import load_data

from bot.utils.setup import load_secrets, load_translations
from bot.villager_bot import VillagerBotCluster


async def main_async(tp: ThreadPoolExecutor):
    secrets = load_secrets()
    translations = load_translations()
    data = load_data()

    villager_bot = VillagerBotCluster(tp, secrets, data, translations)

    async with villager_bot:
        if os.name != "nt":
            # register sigterm handler
            asyncio.get_event_loop().add_signal_handler(
                signal.SIGTERM, lambda: asyncio.ensure_future(villager_bot.close())
            )

        await villager_bot.start()


def main():
    with ThreadPoolExecutor() as tp:
        asyncio.run(main_async(tp))


if __name__ == "__main__":
    main()
