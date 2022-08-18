import asyncio
import os
import signal
import sys

import dotenv

from common.utils.setup import load_data

from karen.karen import MechaKaren
from karen.utils.setup import load_secrets


async def main():
    secrets = load_secrets()
    data = load_data()

    if os.path.exists(".env"):
        env = dotenv.dotenv_values()
        if env.get("CLUSTER_COUNT") != str(secrets.cluster_count):
            print("CLUSTER_COUNT from .env doesn't match with secrets.json!")
            sys.exit(1)

    async with MechaKaren(secrets, data) as karen:
        if os.name != "nt":
            # register sigterm handler
            asyncio.get_event_loop().add_signal_handler(
                signal.SIGTERM, lambda: asyncio.ensure_future(karen.stop)
            )

        await karen.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
