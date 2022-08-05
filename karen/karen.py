from functools import cached_property
from typing import Any, Optional

import asyncpg

from common.coms.packet_handling import PacketHandlerRegistry, handle_packet
from common.coms.packet_type import PacketType
from common.coms.server import Server
from common.models.data import Data
from common.utils.recurring_tasks import RecurringTasksMixin, recurring_task
from common.utils.setup import setup_database_pool
from karen.models.secrets import Secrets
from karen.utils.setup import setup_logging

logger = setup_logging()

class Share:
    """Class which holds any variables only used from packet handlers"""

    def __init__(self, data: Data):
        self.cooldowns = None
        self.econ_paused_users = dict[int, float]()


class MechaKaren(PacketHandlerRegistry, RecurringTasksMixin):
    def __init__(self, secrets: Secrets, data: Data):
        self.secrets = secrets

        self.db: Optional[asyncpg.Pool] = None

        self.server = Server(secrets.karen.host, secrets.karen.port, secrets.karen.auth, self.get_packet_handlers(), logger)

        self.current_cluster_id = 0

        self.v = Share(data)

    @cached_property
    def chunked_shard_ids(self) -> list[list[int]]:
        shard_ids = list(range(self.secrets.shard_count))
        shards_per_cluster = self.secrets.shard_count // self.secrets.cluster_count + 1
        return [shard_ids[i:i+shards_per_cluster] for i in range(self.secrets.cluster_count)]

    async def start(self) -> None:
        self.db = await setup_database_pool(self.secrets.database)

        # nothing past this point
        await self.server.serve()

    async def stop(self) -> None:
        if self.db is not None:
            await self.db.close()

    @handle_packet(PacketType.GET_SHARD_IDS)
    async def handle_get_shard_ids_packet(self) -> list[int]:
        shard_ids = self.chunked_shard_ids[self.current_cluster_id]
        self.current_cluster_id += 1
        return shard_ids

    @handle_packet(PacketType.FETCH_COOLDOWN)
    async def handle_fetch_cooldown_packet(self, command: str, user_id: int) -> dict[str, Any]:
        pass
