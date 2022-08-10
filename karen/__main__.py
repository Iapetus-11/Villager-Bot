import asyncio
import os

import dotenv

from common.utils.setup import load_data

from karen.karen import MechaKaren
from karen.utils.setup import load_secrets

async def main():
    secrets = load_secrets()
    data = load_data()

    if os.path.exists(".env"):
        env = dotenv.dotenv_values()
        if int(env.get("CLUSTER_COUNT")) != secrets.cluster_count:
            print("CLUSTER_COUNT from .env doesn't match with secrets.json!")
            return

    async with MechaKaren(secrets, data) as karen:
        await karen.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
