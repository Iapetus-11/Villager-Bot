import logging
from typing import Any, Optional

import discord
from bot.models.karen.cluster_info import ClusterInfo

from common.coms.client import Client
from common.coms.packet import T_PACKET_DATA, Packet
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType
from common.models.secrets import KarenSecrets

from bot.models.karen.cooldown import Cooldown


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
        if self._client is not None:
            await self._client.close()

        self.logger.info("Disconnected from Karen")

    async def _send(self, packet_type: PacketType, **kwargs: T_PACKET_DATA) -> T_PACKET_DATA:
        resp = await self._client.send(packet_type, kwargs)

        if resp.error:
            raise KarenResponseError(resp)

        return resp.data

    async def _broadcast(
        self, packet_type: PacketType, **kwargs: T_PACKET_DATA
    ) -> list[T_PACKET_DATA]:
        resp = await self._client.broadcast(packet_type, kwargs)

        if resp.error:
            raise KarenResponseError(resp)

        return resp.data

    async def fetch_cluster_info(self) -> ClusterInfo:
        resp = await self._send(PacketType.FETCH_CLUSTER_INFO)
        return ClusterInfo(**resp)

    async def exec_code(self, code: str) -> T_PACKET_DATA:
        return await self._send(PacketType.EXEC_CODE, code=code)

    async def cooldown(self, command: str, user_id: int) -> Cooldown:
        return Cooldown(
            **await self._send(PacketType.COOLDOWN_CHECK_ADD, command=command, user_id=user_id)
        )

    async def cooldown_add(self, command: str, user_id: int) -> None:
        await self._send(PacketType.COOLDOWN_ADD, command=command, user_id=user_id)

    async def cooldown_reset(self, command: str, user_id: int) -> None:
        await self._send(PacketType.COOLDOWN_RESET, command=command, user_id=user_id)

    async def dm_message(self, message: discord.Message) -> None:
        await self._send(
            PacketType.DM_MESSAGE,
            user_id=message.author.id,
            channel_id=message.channel.id,
            message_id=message.id,
            content=message.content,
        )

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

    async def fetch_active_fx(self, user_id: int) -> set[str]:
        return await self._send(PacketType.ACTIVE_FX_FETCH, user_id=user_id)

    async def check_active_fx(self, user_id: int, fx: str) -> bool:
        return await self._send(PacketType.ACTIVE_FX_CHECK, user_id=user_id, fx=fx)

    async def add_active_fx(self, user_id: int, fx: str) -> None:
        await self._send(PacketType.ACTIVE_FX_ADD, user_id=user_id, fx=fx)

    async def remove_active_fx(self, user_id: int, fx: str) -> None:
        await self._send(PacketType.ACTIVE_FX_REMOVE, user_id=user_id, fx=fx)

    async def db_exec(self, query: str, *args: Any) -> None:
        await self._send(PacketType.DB_EXEC, query=query, args=args)

    async def db_exec_many(self, query: str, args: list[list[Any]]) -> None:
        await self._send(PacketType.DB_EXEC_MANY, query=query, args=args)

    async def db_fetch_val(self, query: str, *args: Any) -> Any:
        return await self._send(PacketType.DB_FETCH_VAL, query=query, args=args)

    async def db_fetch_row(self, query: str, *args: Any) -> Optional[dict[str, Any]]:
        return await self._send(PacketType.DB_FETCH_ROW, query=query, args=args)

    async def db_fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        return await self._send(PacketType.DB_FETCH_ALL, query=query, args=args)

    async def get_user_name(self, user_id: int) -> Optional[str]:
        resps = await self._client.broadcast(PacketType.GET_USER_NAME, user_id=user_id)

        for resp in resps:
            if resp is not None:
                return resp

        return None
