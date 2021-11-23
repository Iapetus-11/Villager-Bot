from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
from classyjson import ClassyDict
import asyncio
import asyncpg
import psutil
import arrow

from util.ipc import Server, PacketType, PacketHandlerRegistry, handle_packet
from util.setup import load_secrets, load_data, setup_karen_logging
from util.cooldowns import CooldownManager, MaxConcurrencyManager
from util.code import execute_code, format_exception
from util.misc import MultiLock

from bot import run_cluster


class MechaKaren(PacketHandlerRegistry):
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

        self.logger = setup_karen_logging()
        self.db = None
        self.cooldowns = CooldownManager(self.d.cooldown_rates)
        self.concurrency = MaxConcurrencyManager()
        self.pillage_lock = MultiLock()
        self.server = Server(self.k.manager.host, self.k.manager.port, self.k.manager.auth, self.get_packet_handlers())

        self.shard_ids = tuple(range(self.k.shard_count))
        self.online_shards = set()

        self.eval_env = {"karen": self, **self.v.__dict__}

        self.broadcasts = {}  # {broadcast_id: {ready: asyncio.Event, responses: [response, response,..]}}
        self.dm_messages = {}  # {user_id: {event: asyncio.Event, content: "contents of message"}}
        self.current_id = 0

        self.commands = defaultdict(int)
        self.commands_lock = asyncio.Lock()

        self.commands_task = None
        self.heal_users_task = None
        self.clear_trivia_commands_task = None
        self.reminders_task = None

    @handle_packet(PacketType.MISSING_PACKET)
    async def handle_missing_packet(self, packet: ClassyDict):
        try:
            packet_type = PacketType(packet.get("type"))
        except ValueError:
            packet_type = packet.get("type")

        self.logger.error(f"Missing packet handler for packet type {packet_type}")

    @handle_packet(PacketType.SHARD_READY)
    async def handle_shard_ready_packet(self, packet: ClassyDict):
        self.online_shards.add(packet.shard_id)

        if len(self.online_shards) == len(self.shard_ids):
            self.logger.info(f"\u001b[36;1mALL SHARDS\u001b[0m [0-{len(self.online_shards)-1}] \u001b[36;1mREADY\u001b[0m")

    @handle_packet(PacketType.SHARD_DISCONNECT)
    async def handle_shard_disconnect_packet(self, packet: ClassyDict):
        self.online_shards.discard(packet.shard_id)

    @handle_packet(PacketType.EVAL)
    async def handle_eval_packet(self, packet: ClassyDict):
        try:
            result = eval(packet.code, self.eval_env)
            success = True
        except Exception as e:
            result = format_exception(e)
            success = False

            self.logger.error(result)

        return {"type": PacketType.EVAL_RESPONSE, "result": result, "success": success}

    @handle_packet(PacketType.EXEC)
    async def handle_exec_packet(self, packet: ClassyDict):
        try:
            result = await execute_code(packet.code, self.eval_env)
            success = True
        except Exception as e:
            result = format_exception(e)
            success = False

            self.logger.error(result)

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
        locked = False

        if self.pillage_lock.locked(packet.user_ids):
            locked = True
        else:
            await self.pillage_lock.acquire(packet.user_ids)

        return {
            "type": PacketType.ACQUIRE_PILLAGE_LOCK_RESPONSE,
            "locked": locked,
        }

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

    async def commands_dump_loop(self):
        try:
            while True:
                await asyncio.sleep(60)

                if self.commands:
                    async with self.commands_lock:
                        commands_dump = list(self.commands.items())
                        user_ids = [(user_id,) for user_id in list(self.commands.keys())]

                        self.commands.clear()

                    await self.db.executemany(
                        'INSERT INTO users (user_id) VALUES ($1) ON CONFLICT ("user_id") DO NOTHING', user_ids
                    )  # ensure users are in the database first
                    await self.db.executemany(
                        'INSERT INTO leaderboards (user_id, commands) VALUES ($1, $2) ON CONFLICT ("user_id") DO UPDATE SET "commands" = leaderboards.commands + $2 WHERE leaderboards.user_id = $1',
                        commands_dump,
                    )
        except Exception as e:
            self.logger.error(format_exception(e))

    async def heal_users_loop(self):
        while True:
            await asyncio.sleep(32)

            try:
                await self.db.execute("UPDATE users SET health = health + 1 WHERE health < 20")
            except Exception as e:
                self.logger.error(format_exception(e))

    async def clear_trivia_commands_loop(self):
        while True:
            await asyncio.sleep(10 * 60)

            try:
                self.v.trivia_commands.clear()
            except Exception as e:
                self.logger.error(format_exception(e))

    async def remind_reminders_loop(self):
        while True:
            await asyncio.sleep(5)

            try:
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
            except Exception as e:
                self.logger.error(format_exception(e))

    async def start(self, pp):
        self.db = await asyncpg.create_pool(
            host=self.k.database.host,  # where db is hosted
            database=self.k.database.name,  # name of database
            user=self.k.database.user,  # database username
            password=self.k.database.auth,  # password which goes with user
            max_size=3,
            min_size=1,
        )

        await self.server.start()
        self.cooldowns.start()

        self.commands_task = asyncio.create_task(self.commands_dump_loop())
        self.heal_users_task = asyncio.create_task(self.heal_users_loop())
        self.clear_trivia_commands_task = asyncio.create_task(self.clear_trivia_commands_loop())
        self.reminders_task = asyncio.create_task(self.remind_reminders_loop())

        shard_groups = []
        loop = asyncio.get_event_loop()
        g = self.k.cluster_size

        # calculate max connections to the db server per process allowed
        # postgresql is usually configured to allow 100 max, so we use
        # 75 to leave room for other programs using the db server
        db_pool_size_per = 75 // (self.k.shard_count // g + 1)

        for shard_id_group in [self.shard_ids[i : i + g] for i in range(0, len(self.shard_ids), g)]:
            shard_groups.append(loop.run_in_executor(pp, run_cluster, self.k.shard_count, shard_id_group, db_pool_size_per))

        await asyncio.wait(shard_groups)
        self.cooldowns.stop()

        self.commands_task.cancel()
        self.heal_users_task.cancel()
        self.clear_trivia_commands_task.cancel()
        self.reminders_task.cancel()

        await self.db.close()

    def run(self):
        with ProcessPoolExecutor(self.k.shard_count // self.k.cluster_size + 1) as pp:
            asyncio.run(self.start(pp))
