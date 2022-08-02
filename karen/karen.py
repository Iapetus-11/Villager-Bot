from typing import Optional

import asyncpg

from common.coms.server import Server
from common.coms.packet_handling import PacketHandlerRegistry
from common.utils.recurring_tasks import RecurringTasksMixin, recurring_task
from common.utils.setup import setup_database_pool
from karen.utils.setup import setup_karen_logging
from karen.models.secrets import Secrets


logger = setup_karen_logging()


class MechaKaren(PacketHandlerRegistry, RecurringTasksMixin):
    def __init__(self, secrets: Secrets):
        self.secrets = secrets

        self.db: Optional[asyncpg.Pool] = None

        self.server = Server(secrets.karen.host, secrets.karen.port, secrets.karen.auth, self.get_packet_handlers(), logger)

    async def start(self) -> None:
        self.db = await setup_database_pool(self.secrets.database)

        # nothing past this point
        await self.server.serve()

    async def stop(self) -> None:
        if self.db is not None:
            await self.db.close()
