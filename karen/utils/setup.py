import logging

import asyncpg

from karen.models.secrets import DatabaseSecrets, Secrets


async def setup_database_pool(secrets: DatabaseSecrets) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(
        host=secrets.host,
        port=secrets.port,
        database=secrets.name,
        user=secrets.user,
        password=secrets.auth,
        max_size=secrets.pool_size,
        min_size=1,
    )

    return pool  # type: ignore


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%m-%d-%y %H:%M:%S",
    )
    return logging.getLogger("karen")


def load_secrets() -> Secrets:
    return Secrets.parse_file("karen/secrets.json")
