import asyncio

from common.utils.setup import load_data

from karen.karen import MechaKaren
from karen.utils.setup import load_secrets


async def main():
    secrets = load_secrets()
    data = load_data()

    async with MechaKaren(secrets, data) as karen:
        await karen.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
