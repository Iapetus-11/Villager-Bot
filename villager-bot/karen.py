from concurrent.futures import ProcessPoolExecutor
from classyjson import ClassyDict
import aiofiles
import asyncio
import logging
import arrow

from util.setup import load_secrets, load_data, setup_karen_logging
from util.cooldowns import CooldownManager
from util.ipc import Server, Stream
from util.code import execute_code

from bot import run_shard_group


class MechaKaren:
    class Share:
        def __init__(self):
            self.start_time = arrow.utcnow()

            self.miners = {}  # {user_id: command_count}
            self.active_fx = {}  # {user_id: [effect, potion, effect,..]}

            self.econ_frozen_users = {}  # {user_id: time.time()}
            self.mob_spawn_queue = set()  # Set[ctx, ctx,..]

            self.mc_rcon_cache = {}  # {user_id: rcon client}

    def __init__(self):
        self.k = load_secrets()
        self.d = load_data()
        self.v = self.Share()

        self.logger = setup_karen_logging()
        self.server = Server(self.k.manager.host, self.k.manager.port, self.k.manager.auth, self.handle_packet)
        self.cooldowns = CooldownManager(self.d.cooldown_rates)

        self.shard_ids = tuple(range(self.d.shard_count))
        self.online_shards = set()

        self.eval_env = {"karen": self, **self.v.__dict__}

        self.broadcasts = {}  # broadcast_id: {ready: asyncio.Event, responses: [response, response,..]}
        self.current_id = 0

    async def handle_packet(self, stream: Stream, packet: ClassyDict):
        if packet.type == "shard-ready":
            self.online_shards.add(packet.shard_id)

            if len(self.online_shards) == len(self.shard_ids):
                self.logger.info(f"\u001b[36;1mALL SHARDS\u001b[0m [0-{len(self.online_shards)}] \u001b[36;1mREADY\u001b[0m")
        elif packet.type == "shard-disconnect":
            self.online_shards.discard(packet.shard_id)
        elif packet.type == "eval":
            try:
                result = eval(packet.code, self.eval_env)
                success = True
            except Exception as e:
                result = str(e)
                success = False

            await stream.write_packet({"type": "eval-response", "id": packet.id, "result": result, "success": success})
        elif packet.type == "broadcast-request":
            # broadcasts the packet to every connection including the broadcaster, and waits for responses
            broadcast_id = f"b{self.current_id}"
            self.current_id += 1

            broadcast_packet = {**packet.packet, "id": broadcast_id}
            broadcast_coros = [s.write_packet(broadcast_packet) for s in self.server.connections]
            broadcast = self.broadcasts[broadcast_id] = {
                "ready": asyncio.Event(),
                "responses": [],
                "expects": len(broadcast_coros),
            }

            await asyncio.gather(*broadcast_coros)
            await broadcast["ready"].wait()
            await stream.write_packet({"type": "broadcast-response", "id": packet.id, "responses": broadcast["responses"]})
        elif packet.type == "broadcast-response":
            broadcast = self.broadcasts[packet.id]
            broadcast["responses"].append(packet)

            if len(broadcast["responses"]) == broadcast["expects"]:
                broadcast["ready"].set()
        elif packet.type == "cooldown":
            cooldown_info = self.cooldowns.check(packet.command, packet.user_id)
            await stream.write_packet({"type": "cooldown-info", "id": packet.id, **cooldown_info})
        elif packet.type == "cooldown-add":
            self.cooldowns.add_cooldown(packet.command, packet.user_id)
        elif packet.type == "cooldown-reset":
            self.cooldowns.clear_cooldown(packet.command, packet.user_id)

    async def start(self, pp):
        await self.server.start()
        self.cooldowns.start()

        shard_groups = []
        loop = asyncio.get_event_loop()
        g = self.d.shard_group_size

        for shard_id_group in [self.shard_ids[i : i + g] for i in range(0, len(self.shard_ids), g)]:
            shard_groups.append(loop.run_in_executor(pp, run_shard_group, self.d.shard_count, shard_id_group))

        await asyncio.gather(*shard_groups)
        self.cooldowns.stop()

    def run(self):
        with ProcessPoolExecutor(self.d.shard_count // self.d.shard_group_size + 1) as pp:
            asyncio.run(self.start(pp))
