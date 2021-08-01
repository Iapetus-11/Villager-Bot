from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
from classyjson import ClassyDict
import asyncio
import asyncpg
import arrow

from util.setup import load_secrets, load_data, setup_karen_logging
from util.cooldowns import CooldownManager, MaxConcurrencyManager
from util.ipc import Server, JsonPacketStream, PacketType
from util.code import execute_code, format_exception

from bot import run_cluster


class MechaKaren:
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
        self.server = Server(
            self.k.manager.host,
            self.k.manager.port,
            self.k.manager.auth,
            {
                PacketType.MISSING_PACKET: self.handle_missing_packet,
                PacketType.SHARD_READY: self.handle_shard_ready_packet,
                PacketType.SHARD_DISCONNECT: self.handle_shard_disconnect_packet,
                PacketType.EVAL: self.handle_eval_packet,
                PacketType.EXEC: self.handle_exec_packet,
                PacketType.BROADCAST_REQUEST: self.handle_broadcast_request_packet,
                PacketType.BROADCAST_RESPONSE: self.handle_broadcast_response_packet,
                PacketType.COOLDOWN: self.handle_cooldown_packet,
                PacketType.COOLDOWN_ADD: self.handle_cooldown_add_packet,
                PacketType.COOLDOWN_RESET: self.handle_cooldown_reset_packet,
                PacketType.DM_MESSAGE: self.handle_dm_message_packet,
                PacketType.DM_MESSAGE_REQUEST: self.handle_dm_message_request_packet,
                PacketType.MINE_COMMAND: self.handle_mine_command_packet,
                PacketType.CONCURRENCY_CHECK: self.handle_concurrency_check_packet,
                PacketType.CONCURRENCY_ACQUIRE: self.handle_concurrency_acquire_packet,
                PacketType.CONCURRENCY_RELEASE: self.handle_concurrency_release_packet,
                PacketType.COMMAND_RAN: self.handle_command_ran_packet,
            },
        )

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

    async def handle_missing_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.logger.error(f"Missing packet handler for packet type {packet.type}")

    async def handle_shard_ready_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.online_shards.add(packet.shard_id)

        if len(self.online_shards) == len(self.shard_ids):
            self.logger.info(f"\u001b[36;1mALL SHARDS\u001b[0m [0-{len(self.online_shards)-1}] \u001b[36;1mREADY\u001b[0m")

    async def handle_shard_disconnect_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.online_shards.discard(packet.shard_id)

    async def handle_eval_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        try:
            result = eval(packet.code, self.eval_env)
            success = True
        except Exception as e:
            result = format_exception(e)
            success = False

            self.logger.error(result)

        await stream.write_packet({"type": PacketType.EVAL_RESPONSE, "id": packet.id, "result": result, "success": success})

    async def handle_exec_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        try:
            result = await execute_code(packet.code, self.eval_env)
            success = True
        except Exception as e:
            result = format_exception(e)
            success = False

            self.logger.error(result)

        await stream.write_packet({"type": PacketType.EXEC_RESPONSE, "id": packet.id, "result": result, "success": success})

    async def handle_broadcast_request_packet(self, stream: JsonPacketStream, packet: ClassyDict):
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
        await stream.write_packet(
            {"type": PacketType.BROADCAST_RESPONSE, "id": packet.id, "responses": broadcast["responses"]}
        )

    async def handle_broadcast_response_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        broadcast = self.broadcasts[packet.id]
        broadcast["responses"].append(packet)

        if len(broadcast["responses"]) == broadcast["expects"]:
            broadcast["ready"].set()

    async def handle_cooldown_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        cooldown_info = self.cooldowns.check(packet.command, packet.user_id)
        await stream.write_packet({"type": PacketType.COOLDOWN_RESPONSE, "id": packet.id, **cooldown_info})

    async def handle_cooldown_add_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.cooldowns.add_cooldown(packet.command, packet.user_id)

    async def handle_cooldown_reset_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.cooldowns.clear_cooldown(packet.command, packet.user_id)

    async def handle_dm_message_request_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        entry = self.dm_messages[packet.user_id] = {"event": asyncio.Event(), "content": None}
        await entry["event"].wait()

        self.dm_messages.pop(packet.user_id, None)

        await stream.write_packet({"type": PacketType.DM_MESSAGE, "id": packet.id, "content": entry["content"]})

    async def handle_dm_message_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        entry = self.dm_messages.get(packet.user_id)

        if entry is None:
            return

        entry["content"] = packet.content
        entry["event"].set()

    async def handle_mine_command_packet(self, stream: JsonPacketStream, packet: ClassyDict):  # used for fishing too
        self.v.mine_commands[packet.user_id] += packet.addition
        await stream.write_packet(
            {"type": PacketType.MINE_COMMAND_RESPONSE, "id": packet.id, "current": self.v.mine_commands[packet.user_id]}
        )

    async def handle_concurrency_check_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        await stream.write_packet(
            {
                "type": PacketType.CONCURRENCY_CHECK_RESPONSE,
                "id": packet.id,
                "can_run": self.concurrency.check(packet.command, packet.user_id),
            }
        )

    async def handle_concurrency_acquire_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.concurrency.acquire(packet.command, packet.user_id)

    async def handle_concurrency_release_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        self.concurrency.release(packet.command, packet.user_id)

    async def handle_command_ran_packet(self, stream: JsonPacketStream, packet: ClassyDict):
        async with self.commands_lock:
            self.commands[packet.user_id] += 1

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
        try:
            while True:
                await asyncio.sleep(32)
                await self.db.execute("UPDATE users SET health = health + 1 WHERE health < 20")
        except Exception as e:
            self.logger.error(format_exception(e))

    async def clear_trivia_commands_loop(self):
        try:
            while True:
                await asyncio.sleep(10 * 60)
                self.v.trivia_commands.clear()
        except Exception as e:
            self.logger.error(format_exception(e))

    async def start(self, pp):
        self.db = await asyncpg.create_pool(
            host=self.k.database.host,  # where db is hosted
            database=self.k.database.name,  # name of database
            user=self.k.database.user,  # database username
            password=self.k.database.auth,  # password which goes with user
            max_size=2,
            min_size=1,
        )

        await self.server.start()
        self.cooldowns.start()
        self.commands_task = asyncio.create_task(self.commands_dump_loop())
        self.heal_users_task = asyncio.create_task(self.heal_users_loop())

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
        await self.db.close()

    def run(self):
        with ProcessPoolExecutor(self.k.shard_count // self.k.cluster_size + 1) as pp:
            asyncio.run(self.start(pp))
