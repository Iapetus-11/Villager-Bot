import logging
import time
from typing import Any, Optional

import discord
from bot.models.karen.cluster_info import ClusterInfo

from common.coms.client import Client
from common.coms.packet import T_PACKET_DATA, Packet
from common.coms.packet_handling import PacketHandler
from common.coms.packet_type import PacketType
from common.models.secrets import KarenSecrets

from bot.models.karen.cooldown import Cooldown
from common.utils.validate_return import validate_return


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

    @validate_return
    async def fetch_cluster_info(self) -> ClusterInfo:
        resp = await self._send(PacketType.FETCH_CLUSTER_INFO)
        return ClusterInfo(**resp)

    @validate_return
    async def cooldown(self, command: str, user_id: int) -> Cooldown:
        return Cooldown(
            **await self._send(PacketType.COOLDOWN_CHECK_ADD, command=command, user_id=user_id)
        )

    @validate_return
    async def cooldown_add(self, command: str, user_id: int) -> None:
        await self._send(PacketType.COOLDOWN_ADD, command=command, user_id=user_id)

    @validate_return
    async def cooldown_reset(self, command: str, user_id: int) -> None:
        await self._send(PacketType.COOLDOWN_RESET, command=command, user_id=user_id)

    @validate_return
    async def dm_message(self, message: discord.Message) -> None:
        await self._send(
            PacketType.DM_MESSAGE,
            user_id=message.author.id,
            channel_id=message.channel.id,
            message_id=message.id,
            content=message.content,
        )

    @validate_return
    async def mine_command(self, user_id: int, addition: int) -> int:
        return await self._send(PacketType.MINE_COMMAND, user_id=user_id, addition=addition)

    @validate_return
    async def mine_commands_reset(self, user_id: int) -> None:
        await self._send(PacketType.MINE_COMMANDS_RESET, user_id=user_id)

    @validate_return
    async def check_concurrency(self, command: str, user_id: int) -> bool:
        return await self._send(PacketType.CONCURRENCY_CHECK, command=command, user_id=user_id)

    @validate_return
    async def acquire_concurrency(self, command: str, user_id: int) -> None:
        await self._send(PacketType.CONCURRENCY_ACQUIRE, command=command, user_id=user_id)

    @validate_return
    async def release_concurrency(self, command: str, user_id: int) -> None:
        await self._send(PacketType.CONCURRENCY_RELEASE, command=command, user_id=user_id)

    @validate_return
    async def command_ran(self, user_id: int) -> None:
        await self._send(PacketType.COMMAND_RAN, user_id=user_id)

    @validate_return
    async def check_econ_paused(self, user_id: int) -> bool:
        return await self._send(PacketType.ECON_PAUSE_CHECK, user_id=user_id)

    @validate_return
    async def econ_pause(self, user_id: int) -> None:
        await self._send(PacketType.ECON_PAUSE, user_id=user_id)

    @validate_return
    async def econ_unpause(self, user_id: int) -> None:
        await self._send(PacketType.ECON_PAUSE_UNDO, user_id=user_id)

    @validate_return
    async def fetch_active_fx(self, user_id: int) -> set[str]:
        return await self._send(PacketType.ACTIVE_FX_FETCH, user_id=user_id)

    @validate_return
    async def check_active_fx(self, user_id: int, fx: str) -> bool:
        return await self._send(PacketType.ACTIVE_FX_CHECK, user_id=user_id, fx=fx)

    @validate_return
    async def add_active_fx(self, user_id: int, fx: str) -> None:
        await self._send(PacketType.ACTIVE_FX_ADD, user_id=user_id, fx=fx)

    @validate_return
    async def remove_active_fx(self, user_id: int, fx: str) -> None:
        await self._send(PacketType.ACTIVE_FX_REMOVE, user_id=user_id, fx=fx)

    @validate_return
    async def db_exec(self, query: str, *args: Any) -> None:
        await self._send(PacketType.DB_EXEC, query=query, args=args)

    @validate_return
    async def db_exec_many(self, query: str, args: list[list[Any]]) -> None:
        await self._send(PacketType.DB_EXEC_MANY, query=query, args=args)

    @validate_return
    async def db_fetch_val(self, query: str, *args: Any) -> Any:
        return await self._send(PacketType.DB_FETCH_VAL, query=query, args=args)

    @validate_return
    async def db_fetch_row(self, query: str, *args: Any) -> Optional[dict[str, Any]]:
        return await self._send(PacketType.DB_FETCH_ROW, query=query, args=args)

    @validate_return
    async def db_fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        return await self._send(PacketType.DB_FETCH_ALL, query=query, args=args)

    @validate_return
    async def get_user_name(self, user_id: int) -> Optional[str]:
        resps = await self._client.broadcast(PacketType.GET_USER_NAME, user_id=user_id)

        for resp in resps:
            if resp is not None:
                return resp

        return None

    @validate_return
    async def update_support_server_member_roles(self, user_id: int) -> None:
        await self._broadcast(PacketType.UPDATE_SUPPORT_SERVER_ROLES, user_id=user_id)

    @validate_return
    async def trivia_command(self, user_id: int) -> int:
        return await self._send(PacketType.TRIVIA, user_id=user_id)

    @validate_return
    async def reload_cog(self, cog: str) -> None:
        await self._broadcast(PacketType.RELOAD_COG, cog=cog)

    @validate_return
    async def reload_data(self) -> None:
        await self._broadcast(PacketType.RELOAD_DATA)

    @validate_return
    async def exec_code_all(self, code: str) -> Any:
        return await self._broadcast(PacketType.EXEC_CODE, code=code)

    # @validate_return
    # async def exec_code_karen(self, code: str) -> T_PACKET_DATA:
    #     return await self._send(PacketType.EXEC_CODE, code=code)

    @validate_return
    async def botban_cache_add(self, user_id: int) -> None:
        await self._send(PacketType.BOTBAN_CACHE_ADD, user_id=user_id)

    @validate_return
    async def botban_cache_remove(self, user_id: int) -> None:
        await self._send(PacketType.BOTBAN_CACHE_REMOVE, user_id=user_id)

    @validate_return
    async def lookup_user(self, user_id: int) -> list[list[tuple[int, str]]]:
        return await self._broadcast(PacketType.LOOKUP_USER, user_id=user_id)

    @validate_return
    async def fetch_karen_stats(self) -> list:
        return await self._send(PacketType.FETCH_STATS)

    @validate_return
    async def fetch_clusters_stats(self) -> list[list]:
        return await self._broadcast(PacketType.FETCH_STATS)
    
    @validate_return
    async def fetch_clusters_ping(self) -> float:
        start = time.time()
        await self._broadcast(PacketType.PING)
        return time.time() - start
