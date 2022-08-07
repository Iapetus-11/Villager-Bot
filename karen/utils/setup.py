import logging

import asyncpg

from karen.models.secrets import Secrets, DatabaseSecrets


async def setup_database_pool(secrets: DatabaseSecrets) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=secrets.host,
        port=secrets.port,
        database=secrets.name,
        user=secrets.user,
        password=secrets.auth,
        max_size=secrets.pool_size,
        min_size=1,
    )


def setup_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="[Karen] %(levelname)s: %(message)s")
    return logging.getLogger("karen")


def load_secrets() -> Secrets:
    return Secrets.parse_file("karen/secrets.json")
