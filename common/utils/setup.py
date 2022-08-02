import json

import asyncpg

from common.models.secrets import DatabaseSecrets
from karen.models.secrets import Secrets


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


def get_secrets() -> None:
    with open("karen/secrets.json", "r") as f:
        return Secrets(**json.load(f))
