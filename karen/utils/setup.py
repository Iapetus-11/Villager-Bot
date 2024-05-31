import asyncpg

from karen.models.secrets import DatabaseSecrets, Secrets


async def setup_database_pool(secrets: DatabaseSecrets) -> "asyncpg.Pool[asyncpg.Record]":
    pool = await asyncpg.create_pool(
        host=secrets.host,
        port=secrets.port,
        database=secrets.name,
        user=secrets.user,
        password=secrets.auth,
        max_size=secrets.pool_size,
        min_size=1,
    )

    assert pool is not None

    return pool


def load_secrets() -> Secrets:
    return Secrets.parse_file("karen/secrets.json")
