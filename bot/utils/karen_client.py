import logging
from typing import Optional, Union

import discord

from bot.models.karen.cooldown import Cooldown
from common.coms.client import Client
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType
from common.models.secrets import KarenSecrets
from common.coms.packet import T_PACKET_DATA, Packet


class KarenResponseError(Exception):
    def __init__(self, packet: Packet):
        super().__init__(f"An error was returned from Karen: {packet}")
        self.packet = packet


class KarenClient:
    def __init__(
        self,
        secrets: KarenSecrets,
        packet_handlers: dict[PacketType, PacketHandler],
        logger: logging.Logger,
    ):
        self.secrets = secrets
        self.packet_handlers = packet_handlers
        self.logger = logger.getChild("karen")

        self._client: Optional[Client] = None

    async def connect(self) -> None:
        self._client = Client(
            self.secrets.host, self.secrets.port, self.packet_handlers, self.logger
        )
        await self._client.connect(self.secrets.auth)

    async def disconnect(self) -> None:
        await self._client.close()

    async def _send(self, packet_type: PacketType, **kwargs: T_PACKET_DATA) -> T_PACKET_DATA:
        resp = await self._client.send(packet_type, **kwargs)

        if resp.error:
            raise KarenResponseError(resp)

        return resp.data

    async def fetch_shard_ids(self) -> list[int]:
        return await self._send(PacketType.FETCH_SHARD_IDS)

    async def exec_code(self, code: str) -> T_PACKET_DATA:
        return await self._send(PacketType.EXEC_CODE, code=code)

    async def cooldown(self, command: str, user_id: int) -> Cooldown:
        return Cooldown(**await self._send(
            PacketType.COOLDOWN_CHECK_ADD, command=command, user_id=user_id
        ))

    async def cooldown_add(self, command: str, user_id: int) -> None:
        await self._send(PacketType.COOLDOWN_ADD, command=command, user_id=user_id)
    
    async def cooldown_reset(self, command: str, user_id: int) -> None:
        await self._send(PacketType.COOLDOWN_RESET, command=command, user_id=user_id)

    async def dm_message(self, message: discord.Message) -> None:
        await self._send(PacketType.DM_MESSAGE, user_id=message.author.id, message_id=message.id, content=message.content)

    async def mine_command(self, user_id: int, addition: int) -> int:
        return await self._send(PacketType.MINE_COMMAND, user_id=user_id, addition=addition)

    async def mine_commands_reset(self, user_id: int) -> None:
        await self._send(PacketType.MINE_COMMANDS_RESET, user_id=user_id)

    async def check_concurrency(self, command: str, user_id: int) -> bool:
        return await self._send(PacketType.CONCURRENCY_CHECK, command=command, user_id=user_id)

    async def acquire_concurrency(self, command: str, user_id: int) -> None:
        await self._send(PacketType.CONCURRENCY_ACQUIRE, command=command, user_id=user_id)

    async def release_concurrency(self, command: str, user_id: int) -> None:
        await self._send(PacketType.CONCURRENCY_RELEASE, command=command, user_id=user_id)

    async def command_ran(self, user_id: int) -> None:
        await self._send(PacketType.COMMAND_RAN, user_id=user_id)

    async def fetch_stats(self) -> list:
        return await self._send(PacketType.FETCH_STATS)

    async def check_econ_paused(self, user_id: int) -> bool:
        return await self._send(PacketType.ECON_PAUSE_CHECK, user_id=user_id)

    async def econ_pause(self, user_id: int) -> None:
        await self._send(PacketType.ECON_PAUSE, user_id=user_id)
    
    async def econ_unpause(self, user_id: int) -> None:
        await self._send(PacketType.ECON_PAUSE_UNDO, user_id=user_id)

    async def check_active_fx(self, user_id: int, fx: str) -> bool:
        return await self._send(PacketType.ACTIVE_FX_CHECK, user_id=user_id, fx=fx)

    async def add_active_fx(self, user_id: int, fx: str) -> None:
        await self._send(PacketType.ACTIVE_FX_ADD, user_id=user_id, fx=fx)

    async def remove_active_fx(self, user_id: int, fx: str) -> None:
        await self._send(PacketType.ACTIVE_FX_REMOVE, user_id=user_id, fx=fx)
