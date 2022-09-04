from __future__ import annotations

import asyncio
import itertools
import time
import uuid
from collections import defaultdict
from typing import Any, Optional

import aiohttp
import asyncpg
import psutil

from common.coms.packet import PACKET_DATA_TYPES
from common.coms.packet_handling import PacketHandlerRegistry, handle_packet
from common.coms.packet_type import PacketType
from common.coms.server import Server
from common.data.enums.guild_event_type import GuildEventType
from common.models.data import Data
from common.models.topgg_vote import TopggVote
from common.utils.code import execute_code
from common.utils.misc import chunk_sequence
from common.utils.recurring_tasks import RecurringTasksMixin, recurring_task
from common.utils.setup import setup_logging

from karen.models.secrets import Secrets
from karen.utils.cooldowns import CooldownManager, MaxConcurrencyManager
from karen.utils.setup import setup_database_pool
from karen.utils.shard_ids import ShardIdManager
from karen.utils.topgg import VotingWebhookServer

logger = setup_logging("karen")


class Share:
    """Class which holds any data that clients can access (excluding exec packet)"""

    def __init__(self, data: Data):
        self.command_cooldowns = CooldownManager(data.cooldown_rates)
        self.command_concurrency = MaxConcurrencyManager()
        self.econ_paused_users = dict[int, float]()  # user_id: time paused
        self.mine_commands = defaultdict[int, int](
            int
        )  # user_id: cmd_count, used for fishing as well
        self.trivia_commands = defaultdict[int, int](int)  # user_id: cmd_count
        self.command_counts = defaultdict[int, int](int)  # user_id: cmd_count
        self.active_fx = defaultdict[int, set[str]](set[str])  # user_id: set[fx]
        self.current_cluster_id = 0


class MechaKaren(PacketHandlerRegistry, RecurringTasksMixin):
    def __init__(self, secrets: Secrets, data: Data):
        self.k = secrets

        self._db: Optional[asyncpg.Pool] = None

        self.ready_event = asyncio.Event()

        self.server = Server(
            secrets.karen.host,
            secrets.karen.port,
            secrets.karen.auth,
            self.get_packet_handlers(),
            logger,
            self._connect_callback,
            self._disconnect_callback,
        )

        self.votehook_server = VotingWebhookServer(
            self.k.topgg_webhook, self._vote_callback, logger
        )

        self.v = Share(data)

        self.aiohttp: Optional[aiohttp.ClientSession] = None

        self.shard_ids = ShardIdManager(self.k.shard_count, self.k.cluster_count)

        self._did_initial_load = False
        self._did_stop = False

        RecurringTasksMixin.__init__(self, logger.getChild("loops"))

    @property
    def db(self) -> asyncpg.Pool:
        if self._db is None:
            raise RuntimeError("Database has not yet been initialized")

        return self._db

    @db.setter
    def db(self, value: asyncpg.Pool) -> None:
        self._db = value

    async def serve(self) -> None:
        logger.info("Starting Karen...")

        self.db = await setup_database_pool(self.k.database)
        logger.info(
            "Initialized database connection pool for server %s:%s",
            self.k.database.host,
            self.k.database.port,
        )

        self.aiohttp = aiohttp.ClientSession()
        logger.info("Initialized aiohttp ClientSession")

        await self.votehook_server.start()

        # nothing past this point
        await self.server.serve(self._on_ready)

    async def stop(self) -> None:
        logger.info("Shutting down Karen...")

        await self.server.stop()
        logger.info("Stopped websocket server")

        self.cancel_recurring_tasks()

        if self._db is not None:
            await self.db.close()
            logger.info("Closed database pool")

        if self.aiohttp is not None:
            await self.aiohttp.close()
            logger.info("Closed aiohttp ClientSession")

        await self.votehook_server.stop()

        self._did_stop = True

    async def __aenter__(self) -> MechaKaren:
        return self

    async def __aexit__(self, exc_type: type, exc: Exception, tb: Any) -> None:
        if not self._did_stop:
            await self.stop()

        if exc:
            raise exc

    async def _vote_callback(self, vote: TopggVote) -> None:
        await self.ready_event.wait()
        await self.server.broadcast(PacketType.TOPGG_VOTE, {"vote": vote})

    async def _connect_callback(self, ws_id: uuid.UUID) -> None:
        if len(self.server._connections) == self.k.cluster_count and not self._did_initial_load:
            await self._update_guild_diffs()
            self._did_initial_load = True

    async def _disconnect_callback(self, ws_id: uuid.UUID) -> None:
        self.shard_ids.release(ws_id)

    def _on_ready(self) -> None:
        self.ready_event.set()
        self.start_recurring_tasks()

    async def _update_guild_diffs(self):
        logger.info("Updating guild events table with missed joins and leaves...")

        current_guilds_db = await self.db.fetch(
            """SELECT COALESCE(js.guild_id, ls.guild_id) AS guild_id FROM (
    SELECT guild_id, COUNT(*) AS c FROM guild_events WHERE event_type = 1 GROUP BY guild_id) js
FULL JOIN (
    SELECT guild_id, COUNT(*) AS c FROM guild_events WHERE event_type = 2 GROUP BY guild_id) ls
ON js.guild_id = ls.guild_id WHERE (COALESCE(js.c, 0) - COALESCE(ls.c, 0)) > 0"""
        )

        current_guilds_db: set[int] = {r["guild_id"] for r in current_guilds_db}

        current_guilds = set[int](
            itertools.chain.from_iterable(await self.server.broadcast(PacketType.FETCH_GUILD_IDS))
        )

        missed_guild_joins = current_guilds - current_guilds_db
        missed_guild_leaves = current_guilds_db - current_guilds

        await self.db.executemany(
            "INSERT INTO guild_events (guild_id, event_type, member_count, total_count) VALUES ($1, $2, 0, 0)",
            [(guild_id, GuildEventType.GUILD_JOIN.value) for guild_id in missed_guild_joins],
        )
        await self.db.executemany(
            "INSERT INTO guild_events (guild_id, event_type, member_count, total_count) VALUES ($1, $2, 0, 0)",
            [(guild_id, GuildEventType.GUILD_LEAVE.value) for guild_id in missed_guild_leaves],
        )

        logger.info("Done updating guild events table")

    @classmethod
    def _transform_query_result(cls, result: Any) -> Any:
        if isinstance(result, list):
            return [cls._transform_query_result(r) for r in result]

        if isinstance(result, asyncpg.Record):
            return {k: v for k, v in result.items()}

        return result

    ###### loops ###############################################################

    @recurring_task(minutes=2)
    async def loop_clear_dead(self):
        self.v.command_cooldowns.clear_dead()

    @recurring_task(minutes=1)
    async def loop_dump_command_counts(self):
        if not self.v.command_counts:
            return

        commands_dump = list(self.v.command_counts.items())
        user_ids = [(user_id,) for user_id in self.v.command_counts.keys()]
        self.v.command_counts.clear()

        # ensure users are in db first
        await self.db.executemany(
            'INSERT INTO users (user_id) VALUES ($1) ON CONFLICT ("user_id") DO NOTHING', user_ids
        )

        await self.db.executemany(
            'INSERT INTO leaderboards (user_id, commands, week_commands) VALUES ($1, $2, $2) ON CONFLICT ("user_id") DO UPDATE SET "commands" = leaderboards.commands + $2, "week_commands" = leaderboards.week_commands + $2 WHERE leaderboards.user_id = $1',
            commands_dump,
        )

    @recurring_task(seconds=32)
    async def loop_heal_users(self):
        await self.db.execute("UPDATE users SET health = health + 1 WHERE health < 20")

    @recurring_task(minutes=10)
    async def loop_clear_trivia_commands(self):
        self.v.trivia_commands.clear()

    @recurring_task(seconds=5, sleep_first=False)
    async def loop_remind_reminders(self):
        reminders = await self.db.fetch(
            "DELETE FROM reminders WHERE at <= NOW() RETURNING channel_id, user_id, message_id, reminder"
        )

        broadcast_coros = [self.server.broadcast(PacketType.REMINDER, {**r}) for r in reminders]

        for coros_chunk in chunk_sequence(broadcast_coros, 4):
            await asyncio.wait(coros_chunk)

    @recurring_task(minutes=30, sleep_first=False)
    async def loop_clear_weekly_leaderboards(self):
        await self.db.execute(
            "UPDATE leaderboards SET week_emeralds = 0, week_commands = 0, week = DATE_TRUNC('WEEK', NOW()) WHERE DATE_TRUNC('WEEK', NOW()) > week"
        )

    @recurring_task(hours=1, sleep_first=True)
    async def loop_topgg_stats(self):
        responses = await self.server.broadcast(PacketType.FETCH_GUILD_COUNT)

        await self.aiohttp.post(
            f"https://top.gg/api/bots/{self.k.bot_id}/stats",
            headers={"Authorization": self.k.topgg_api},
            json={"server_count": str(sum(responses))},
        )

    ###### packet handlers #####################################################

    @handle_packet(PacketType.EXEC_CODE)
    async def packet_exec(self, code: str):
        result = await execute_code(code, {"karen": self, "v": self.v})

        if not isinstance(result, PACKET_DATA_TYPES):
            result = repr(result)

        return result

    @handle_packet(PacketType.FETCH_CLUSTER_INFO)
    async def packet_fetch_cluster_info(self, ws_id: uuid.UUID):
        self.v.current_cluster_id += 1
        return {
            "shard_ids": self.shard_ids.take(ws_id),
            "shard_count": self.k.shard_count,
            "cluster_id": self.v.current_cluster_id - 1,
        }

    @handle_packet(PacketType.COOLDOWN_CHECK_ADD)
    async def packet_cooldown(self, command: str, user_id: int):
        can_run, remaining = self.v.command_cooldowns.check_add_cooldown(command, user_id)
        return {"can_run": can_run, "remaining": remaining}

    @handle_packet(PacketType.COOLDOWN_ADD)
    async def packet_cooldown_add(self, command: str, user_id: int):
        self.v.command_cooldowns.add_cooldown(command, user_id)

    @handle_packet(PacketType.COOLDOWN_RESET)
    async def packet_cooldown_reset(self, command: str, user_id: int):
        self.v.command_cooldowns.clear_cooldown(command, user_id)

    @handle_packet(PacketType.DM_MESSAGE)
    async def packet_dm_message(
        self, user_id: int, channel_id: int, message_id: int, content: Optional[str]
    ):
        await self.server.broadcast(
            PacketType.DM_MESSAGE,
            {
                "user_id": user_id,
                "channel_id": channel_id,
                "message_id": message_id,
                "content": content,
            },
        )

    @handle_packet(PacketType.MINE_COMMAND)
    async def packet_mine_command(self, user_id: int, addition: int):
        self.v.mine_commands[user_id] += addition
        return self.v.mine_commands[user_id]

    @handle_packet(PacketType.MINE_COMMANDS_RESET)
    async def packet_mine_commands_reset(self, user_id: int):
        self.v.mine_commands.pop(user_id, None)

    @handle_packet(PacketType.CONCURRENCY_CHECK)
    async def packet_concurrency_check(self, command: str, user_id: int):
        return self.v.command_concurrency.check(command, user_id)

    @handle_packet(PacketType.CONCURRENCY_ACQUIRE)
    async def packet_concurrency_acquire(self, command: str, user_id: int):
        self.v.command_concurrency.acquire(command, user_id)

    @handle_packet(PacketType.CONCURRENCY_RELEASE)
    async def packet_concurrency_release(self, command: str, user_id: int):
        self.v.command_concurrency.release(command, user_id)

    @handle_packet(PacketType.COMMAND_RAN)
    async def packet_command_ran(self, user_id: int):
        self.v.command_counts[user_id] += 1

    @handle_packet(PacketType.FETCH_STATS)
    async def handle_fetch_stats_packet(self):
        proc = psutil.Process()
        with proc.oneshot():
            mem_usage = proc.memory_full_info().uss
            threads = proc.num_threads()

        return [mem_usage, threads, len(asyncio.all_tasks())] + [0] * 7

    @handle_packet(PacketType.ECON_PAUSE_CHECK)
    async def packet_econ_pause_check(self, user_id: int):
        return user_id in self.v.econ_paused_users

    @handle_packet(PacketType.ECON_PAUSE)
    async def packet_econ_pause(self, user_id: int):
        self.v.econ_paused_users[user_id] = time.time()

    @handle_packet(PacketType.ECON_PAUSE_UNDO)
    async def packet_econ_pause_undo(self, user_id: int):
        self.v.econ_paused_users.pop(user_id, None)

    @handle_packet(PacketType.ACTIVE_FX_FETCH)
    async def packet_active_fx_fetch(self, user_id: int):
        return self.v.active_fx[user_id]

    @handle_packet(PacketType.ACTIVE_FX_CHECK)
    async def packet_active_fx_check(self, user_id: int, fx: str):
        return fx.lower() in self.v.active_fx[user_id]

    @handle_packet(PacketType.ACTIVE_FX_ADD)
    async def packet_active_fx_add(self, user_id: int, fx: str):
        self.v.active_fx[user_id].add(fx.lower())

    @handle_packet(PacketType.ACTIVE_FX_REMOVE)
    async def packet_active_fx_remove(self, user_id: int, fx: str):
        try:
            self.v.active_fx[user_id].remove(fx.lower())
        except KeyError:
            pass

    @handle_packet(PacketType.DB_EXEC)
    async def packet_db_exec(self, query: str, args: list[Any]):
        await self.db.execute(query, *args)

    @handle_packet(PacketType.DB_EXEC_MANY)
    async def packet_db_exec_many(self, query: str, args: list[list[Any]]):
        await self.db.executemany(query, args)

    @handle_packet(PacketType.DB_FETCH_VAL)
    async def packet_db_fetch_one(self, query: str, args: list[Any]):
        return self._transform_query_result(await self.db.fetchval(query, *args))

    @handle_packet(PacketType.DB_FETCH_ROW)
    async def packet_db_fetch_row(self, query: str, args: list[Any]):
        return self._transform_query_result(await self.db.fetchrow(query, *args))

    @handle_packet(PacketType.DB_FETCH_ALL)
    async def packet_db_fetch_all(self, query: str, args: list[Any]):
        return self._transform_query_result(await self.db.fetch(query, *args))

    @handle_packet(PacketType.TRIVIA)
    async def packet_trivia(self, user_id: int):
        commands = self.v.trivia_commands[user_id]
        self.v.trivia_commands[user_id] += 1
        return commands

    @handle_packet(PacketType.SHUTDOWN)
    async def packet_shutdown(self):
        await self.server.raw_broadcast(PacketType.SHUTDOWN)
        await self.stop()
