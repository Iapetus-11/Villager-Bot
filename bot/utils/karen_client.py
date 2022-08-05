import logging
from typing import Optional
from bot.models.karen.cooldown import Cooldown
from common.coms.client import Client
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType
from common.models.secrets import KarenSecrets


class KarenClient:
    def __init__(self, secrets: KarenSecrets, packet_handlers: dict[PacketType, PacketHandler], logger: logging.Logger):
        self.secrets = secrets
        self.packet_handlers = packet_handlers
        self.logger = logger

        self.client: Optional[Client] = None

    async def connect(self) -> None:
        self.client = Client(self.secrets.host, self.secrets.port, self.packet_handlers, self.logger)
        await self.client.connect(self.secrets.auth)

    async def disconnect(self) -> None:
        await self.client.close()

    async def fetch_shard_ids(self) -> list[int]:
        resp = await self.client.send(PacketType.GET_SHARD_IDS)
        return resp.data["shard_ids"]

    async def fetch_cooldown(self, command: str, user_id: int) -> Cooldown:
        resp = await self.client.send(PacketType.FETCH_COOLDOWN, {"command": command, "user_id": user_id})
        return Cooldown(**resp)

    async def check_concurrency(self, command: str, user_id: int) -> bool:
        resp = await self.client.send(PacketType.CONCURRENCY_CHECK, {"command": command, "user_id": user_id})
        return resp.data["can_run"]

    async def acquire_concurrency(self, command: str, user_id: int) -> None:
        await self.client.send(PacketType.CONCURRENCY_ACQUIRE, {"command": command, "user_id": user_id})

    async def check_econ_paused(self, user_id: int) -> bool:
        resp = await self.client.send(PacketType.ECON_PAUSE_CHECK, {"user_id": user_id})
        return resp.data["paused"]
