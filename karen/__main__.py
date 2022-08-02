import asyncio

from common.utils.setup import get_secrets
from karen.karen import MechaKaren


def main():
    karen = MechaKaren(get_secrets())

    try:
        asyncio.run(karen.start())
    finally:
        asyncio.run(karen.stop())


if __name__ == "__main__":
    main()
