import asyncio

from common.utils.setup import load_data

from karen.karen import MechaKaren
from karen.utils.setup import load_secrets


def main():
    secrets = load_secrets()
    data = load_data()

    karen = MechaKaren(secrets, data)

    try:
        asyncio.run(karen.start())
    finally:
        asyncio.run(karen.stop())


if __name__ == "__main__":
    main()
