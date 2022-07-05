import asyncio
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Set

import arrow
import asyncpg
import psutil
from bot import run_cluster
from classyjson import ClassyDict
from util.code import execute_code, format_exception
from util.cooldowns import CooldownManager, MaxConcurrencyManager
from util.ipc import PacketHandlerRegistry, PacketType, Server, handle_packet
from util.misc import MultiLock
from util.recurring_task import RecurringTasksMixin, recurring_task
from util.setup import load_data, load_secrets, setup_karen_logging, setup_database_pool

logger = setup_karen_logging()


class MechaKaren(PacketHandlerRegistry, RecurringTasksMixin):
    class Share:
        def __init__(self):
            self.start_time = arrow.utcnow()

            self.mine_commands = defaultdict(int)  # {user_id: command_count}, also used for fishing btw
            self.trivia_commands = defaultdict(int)  # {user_id: trivia_command_count}
            self.active_effects = defaultdict(set)  # {user_id: [effect, potion, effect,..]}
            self.pillages = defaultdict(int)  # {user_id: num_successful_pillages}

            self.econ_paused_users = {}  # {user_id: time.time()}

    def __init__(self):
        self.k = load_secrets()
        self.d = load_data()
        self.v = self.Share()

        self.db: asyncpg.Pool = None
        self.cooldowns = CooldownManager(self.d.cooldown_rates)
        self.concurrency = MaxConcurrencyManager()
        self.pillage_lock = MultiLock()
        self.server = Server(self.k.manager.host, self.k.manager.port, self.k.manager.auth, self.get_packet_handlers())

        self.shard_ids = list(range(self.k.shard_count))
        self.online_clusters: Set[int] = set()

        self.eval_env: Dict[str, Any] = {"karen": self, **self.v.__dict__}

        self.broadcasts: Dict[
            str, Dict[str, Any]
        ] = {}  # {broadcast_id: {ready: asyncio.Event, responses: [response, response,..]}}
        self.dm_messages: Dict[int, Dict[str, Any]] = {}  # {user_id: {event: asyncio.Event, content: "contents of message"}}
        self.current_id = 0

        self.commands = defaultdict(int)
        self.commands_lock = asyncio.Lock()

    @handle_packet(PacketType.MISSING_PACKET)
    async def handle_missing_packet(self, packet: ClassyDict):
        try:
            packet_type = PacketType(packet.get("type"))
        except ValueError:
            packet_type = packet.get("type")

        logger.error(f"Missing packet handler for packet type {packet_type}")

    @handle_packet(PacketType.CLUSTER_READY)
    async def handle_cluster_ready_packet(self, packet: ClassyDict):
        self.online_clusters.add(packet.cluster_id)

        if len(self.online_clusters) == self.k.cluster_count:
            logger.info(f"\u001b[36;1mALL CLUSTERS\u001b[0m [0-{self.k.cluster_count-1}] \u001b[36;1mREADY\u001b[0m")

    @handle_packet(PacketType.EVAL)
    async def handle_eval_packet(self, packet: ClassyDict):
        try:
            result = eval(packet.code, self.eval_env)
            success = True
        except Exception as e:
            result = format_exception(e)
            success = False

            logger.error(result)

        return {"type": PacketType.EVAL_RESPONSE, "result": result, "success": success}

    @handle_packet(PacketType.EXEC)
    async def handle_exec_packet(self, packet: ClassyDict):
        try:
            result = await execute_code(packet.code, self.eval_env)
            success = True
        except Exception as e:
            result = format_exception(e)
            success = False

            logger.error(result)

        return {"type": PacketType.EXEC_RESPONSE, "result": result, "success": success}

    @handle_packet(PacketType.BROADCAST_REQUEST)
    async def handle_broadcast_request_packet(self, packet: ClassyDict):
        """broadcasts the packet to every connection including the broadcaster, and waits for responses"""

        broadcast_id = f"b{self.current_id}"
        self.current_id += 1

        broadcast_packet = {**packet.packet, "id": broadcast_id}
        broadcast_coros = [s.write_packet(broadcast_packet) for s in self.server.connections]
        broadcast = self.broadcasts[broadcast_id] = {
            "ready": asyncio.Event(),
            "responses": [],
            "expects": len(broadcast_coros),
        }

        await asyncio.wait(broadcast_coros)
        await broadcast["ready"].wait()

        return {"type": PacketType.BROADCAST_RESPONSE, "responses": broadcast["responses"]}

    @handle_packet(PacketType.BROADCAST_RESPONSE)
    async def handle_broadcast_response_packet(self, packet: ClassyDict):
        broadcast = self.broadcasts[packet.id]
        broadcast["responses"].append(packet)

        if len(broadcast["responses"]) == broadcast["expects"]:
            broadcast["ready"].set()

    @handle_packet(PacketType.COOLDOWN)
    async def handle_cooldown_packet(self, packet: ClassyDict):
        cooldown_info = self.cooldowns.check(packet.command, packet.user_id)
        return {"type": PacketType.COOLDOWN_RESPONSE, **cooldown_info}

    @handle_packet(PacketType.COOLDOWN_ADD)
    async def handle_cooldown_add_packet(self, packet: ClassyDict):
        self.cooldowns.add_cooldown(packet.command, packet.user_id)

    @handle_packet(PacketType.COOLDOWN_RESET)
    async def handle_cooldown_reset_packet(self, packet: ClassyDict):
        self.cooldowns.clear_cooldown(packet.command, packet.user_id)

    @handle_packet(PacketType.DM_MESSAGE_REQUEST)
    async def handle_dm_message_request_packet(self, packet: ClassyDict):
        entry = self.dm_messages[packet.user_id] = {"event": asyncio.Event(), "content": None}
        await entry["event"].wait()

        self.dm_messages.pop(packet.user_id, None)

        return {"type": PacketType.DM_MESSAGE, "content": entry["content"]}

    @handle_packet(PacketType.DM_MESSAGE)
    async def handle_dm_message_packet(self, packet: ClassyDict):
        entry = self.dm_messages.get(packet.user_id)

        if entry is None:
            return

        entry["content"] = packet.content
        entry["event"].set()

    @handle_packet(PacketType.MINE_COMMAND)
    async def handle_mine_command_packet(self, packet: ClassyDict):  # used for fishing too
        self.v.mine_commands[packet.user_id] += packet.addition
        return {"type": PacketType.MINE_COMMAND_RESPONSE, "current": self.v.mine_commands[packet.user_id]}

    @handle_packet(PacketType.MINE_COMMANDS_RESET)
    async def handle_mine_commands_reset_packet(self, packet: ClassyDict):
        self.v.mine_commands[packet.user] = 0

    @handle_packet(PacketType.CONCURRENCY_CHECK)
    async def handle_concurrency_check_packet(self, packet: ClassyDict):
        return {
            "type": PacketType.CONCURRENCY_CHECK_RESPONSE,
            "can_run": self.concurrency.check(packet.command, packet.user_id),
        }

    @handle_packet(PacketType.CONCURRENCY_ACQUIRE)
    async def handle_concurrency_acquire_packet(self, packet: ClassyDict):
        self.concurrency.acquire(packet.command, packet.user_id)

    @handle_packet(PacketType.CONCURRENCY_RELEASE)
    async def handle_concurrency_release_packet(self, packet: ClassyDict):
        self.concurrency.release(packet.command, packet.user_id)

    @handle_packet(PacketType.COMMAND_RAN)
    async def handle_command_ran_packet(self, packet: ClassyDict):
        async with self.commands_lock:
            self.commands[packet.user_id] += 1

    @handle_packet(PacketType.ACQUIRE_PILLAGE_LOCK)
    async def handle_acquire_pillage_lock_packet(self, packet: ClassyDict):
        await self.pillage_lock.acquire(packet.user_ids)
        return {}

    @handle_packet(PacketType.RELEASE_PILLAGE_LOCK)
    async def handle_release_pillage_lock_packet(self, packet: ClassyDict):
        self.pillage_lock.release(packet.user_ids)

    @handle_packet(PacketType.PILLAGE)
    async def handle_pillage_packet(self, packet: ClassyDict):
        self.v.pillages[packet.pillager] += 1
        return {"pillager": self.v.pillages[packet.pillager] - 1, "victim": self.v.pillages[packet.victim] - 1}

    @handle_packet(PacketType.FETCH_STATS)
    async def handle_fetch_stats_packet(self, packet: ClassyDict):
        proc = psutil.Process()
        with proc.oneshot():
            mem_usage = proc.memory_full_info().uss
            threads = proc.num_threads()

        return {"type": PacketType.STATS_RESPONSE, "stats": [mem_usage, threads, len(asyncio.all_tasks())] + [0] * 7}

    @handle_packet(PacketType.TRIVIA)
    async def handle_trivia_packet(self, packet: ClassyDict):
        self.v.trivia_commands[packet.author] += 1
        return {"do_reward": self.v.trivia_commands[packet.author] < 5}

    @recurring_task(seconds=60, logger=logger)
    async def commands_dump_loop(self):
        if not self.commands:
            return

        async with self.commands_lock:
            commands_dump = list(self.commands.items())
            user_ids = [(user_id,) for user_id in list(self.commands.keys())]

            self.commands.clear()

        await self.db.executemany(
            'INSERT INTO users (user_id) VALUES ($1) ON CONFLICT ("user_id") DO NOTHING', user_ids
        )  # ensure users are in the database first
        await self.db.executemany(
            'INSERT INTO leaderboards (user_id, commands, week_commands) VALUES ($1, $2, $2) ON CONFLICT ("user_id") DO UPDATE SET "commands" = leaderboards.commands + $2, "week_commands" = leaderboards.week_commands + $2 WHERE leaderboards.user_id = $1',
            commands_dump,
        )

    @recurring_task(seconds=32, logger=logger)
    async def heal_users_loop(self):
        await self.db.execute("UPDATE users SET health = health + 1 WHERE health < 20")

    @recurring_task(minutes=10, logger=logger)
    async def clear_trivia_commands_loop(self):
        self.v.trivia_commands.clear()

    @recurring_task(seconds=5, logger=logger)
    async def remind_reminders_loop(self):
        reminders = await self.db.fetch(
            "DELETE FROM reminders WHERE at <= NOW() RETURNING channel_id, user_id, message_id, reminder"
        )

        for reminder in reminders:
            broadcast_id = f"b{self.current_id}"
            self.current_id += 1

            broadcast_packet = {"type": PacketType.REMINDER, "id": broadcast_id, **reminder}
            broadcast_coros = [s.write_packet(broadcast_packet) for s in self.server.connections]
            broadcast = self.broadcasts[broadcast_id] = {
                "ready": asyncio.Event(),
                "responses": [],
                "expects": len(broadcast_coros),
            }

            await asyncio.wait(broadcast_coros)
            await broadcast["ready"].wait()

    @recurring_task(hours=1, logger=logger)
    async def clear_weekly_leaderboards_loop(self):
        await self.db.execute(
            "UPDATE leaderboards SET week_emeralds = 0, week_commands = 0, week = DATE_TRUNC('WEEK', NOW()) WHERE DATE_TRUNC('WEEK', NOW()) > week"
        )

    async def start(self, pp):
        self.db = await setup_database_pool(self.k, max_size=3)

        await self.server.start()
        self.cooldowns.start()

        self.commands_dump_loop.start()
        self.heal_users_loop.start()
        self.clear_trivia_commands_loop.start()
        self.remind_reminders_loop.start()
        self.clear_weekly_leaderboards_loop.start()

        loop = asyncio.get_event_loop()

        cluster_size: int = self.k.shard_count // self.k.cluster_count  # how many shards per cluster
        clusters: List[asyncio.Future] = []
        shard_ids_chunked = [self.shard_ids[i : i + cluster_size] for i in range(0, self.k.shard_count, cluster_size)]

        # create and run clusters
        for cluster_id, shard_ids in enumerate(shard_ids_chunked):
            clusters.append(loop.run_in_executor(pp, run_cluster, cluster_id, self.k.shard_count, shard_ids, self.k.db.cluster_pool_size))

        await asyncio.wait(clusters)

        self.cooldowns.stop()

        self.commands_dump_loop.cancel()
        self.heal_users_loop.cancel()
        self.clear_trivia_commands_loop.cancel()
        self.remind_reminders_loop.cancel()
        self.clear_weekly_leaderboards_loop.cancel()

        await self.db.close()

    def run(self):
        with ProcessPoolExecutor(self.k.cluster_count) as pp:
            asyncio.run(self.start(pp))
