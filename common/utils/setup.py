import asyncpg
from common.models.data import Data

from common.models.secrets import DatabaseSecrets


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


def load_data() -> Data:
    return Data.parse_file("common/data/data.json")

