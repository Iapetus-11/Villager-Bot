import asyncio

from common.utils.setup import load_secrets
from karen.karen import MechaKaren


def main():
    karen = MechaKaren(load_secrets())

    try:
        asyncio.run(karen.start())
    finally:
        asyncio.run(karen.stop())


if __name__ == "__main__":
    main()
