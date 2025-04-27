# ruff: noqa: T201

import asyncio
import os
import signal
import sys

from bot.utils.setup import load_data

from bot.utils.add_cython_ext import add_cython_ext
from bot.utils.setup import load_secrets, load_translations
from bot.villager_bot import VillagerBotCluster


async def main_async() -> None:
    secrets = load_secrets()
    data = load_data()
    translations = load_translations(data.disabled_translations)

    villager_bot = VillagerBotCluster(secrets, data, translations)

    async with villager_bot:
        if os.name != "nt":
            # register sigterm handler
            asyncio.get_event_loop().add_signal_handler(
                signal.SIGTERM,
                lambda: asyncio.create_task(villager_bot.close()),
            )

        await villager_bot.start()


def main(args: list[str]) -> None:
    if not vars(sys.modules[__name__])["__package__"]:
        print("Villager Bot must be ran as a module (using the -m flag)")
        sys.exit(1)

    add_cython_ext()

    for required_path in ["tmp", "fonts"]:
        if not os.path.exists(required_path):
            os.mkdir(required_path)

    if "--build-cython-only" not in args:
        asyncio.run(main_async())


if __name__ == "__main__":
    main(sys.argv[1:])
