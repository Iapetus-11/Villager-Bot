import asyncio
import os
import signal
import sys

import psutil

from common.utils.setup import load_data

from karen.karen import MechaKaren
from karen.utils.setup import load_secrets


async def async_main():
    secrets = load_secrets()
    data = load_data()

    # if os.path.exists(".env"):
    #     env = dotenv.dotenv_values()
    #     if env.get("CLUSTER_COUNT") != str(secrets.cluster_count):
    #         print("CLUSTER_COUNT from .env doesn't match with secrets.json!")
    #         sys.exit(1)

    async with MechaKaren(secrets, data) as karen:
        if os.name != "nt":
            # register sigterm handler
            asyncio.get_event_loop().add_signal_handler(
                signal.SIGTERM, lambda: asyncio.create_task(karen.stop)
            )

        await karen.serve()


def main():
    if not vars(sys.modules[__name__])["__package__"]:
        print("Karen must be ran as a module (using the -m flag)")
        sys.exit(1)

    # start thread which handles this
    psutil.getloadavg()

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
