from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import asyncio
import time

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.setup import load_text, load_secrets, load_data
from util.cooldowns import CommandOnCooldown2
from util.code import execute_code
from util.ipc import Client


def run_shard_group(shard_count: int, shard_ids: list) -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    shard_group = VillagerBotShardGroup(shard_count, shard_ids)
    shard_group.run()


class VillagerBotShardGroup(commands.AutoShardedBot):
    def __init__(self, shard_count: int, shard_ids: list) -> None:
        super().__init__(
            command_prefix=self.get_prefix,
            intents=villager_bot_intents(),
            shard_count=shard_count,
            shard_ids=shard_ids,
        )

        self.start_time = time.time()

        self.k = load_secrets()
        self.d = load_data()
        self.l = load_text()

        self.cog_list = ["cogs.core.events", "cogs.core.loops", "cogs.core.share", "cogs.commands.owner"]

        self.logger = setup_logging(self.shard_ids)
        self.ipc = Client(self.k.manager.host, self.k.manager.port, self.handle_broadcast)
        self.aiohttp = aiohttp.ClientSession()
        self.db = None

        self.ban_cache = set()
        self.language_cache = {}
        self.prefix_cache = {}
        self.disabled_commands = {}
        self.replies_cache = set()

        self.add_check(self.check_global)

    @property
    def eval_env(self):
        return {
            **globals(),
            "bot": self,
            "self": self,
            "k": self.k,
            "d": self.d,
            "l": self.l,
            "aiohttp": self.aiohttp,
            "db": self.db,
        }

    async def start(self, *args, **kwargs):
        await self.ipc.connect(self.k.manager.auth, self.shard_ids)
        self.db = await setup_database(self.k)

        for cog in self.cog_list:
            self.load_extension(cog)

        await super().start(*args, **kwargs)

    async def close(self, *args, **kwargs):
        await self.ipc.close()
        await self.db.close()
        await self.aiohttp.close()

        await super().close(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(self.k.discord_token, *args, **kwargs)

    async def handle_broadcast(self, packet: ClassyDict) -> None:
        if packet.type == "eval":
            try:
                result = eval(packet.code, self.eval_env)
                success = True
            except Exception as e:
                result = str(e)
                success = False

            await self.ipc.send({"type": "broadcast-response", "id": packet.id, "result": result, "success": success})
        elif packet.type == "exec":
            try:
                result = await execute_code(packet.code, self.eval_env)
                success = True
            except Exception as e:
                result = str(e)
                success = False

            await self.ipc.send({"type": "broadcast-response", "id": packet.id, "result": result, "success": success})

    def get_prefix(self, ctx: commands.Context) -> str:
        if ctx.guild:
            return self.prefix_cache.get(ctx.guild.id, self.d.default_prefix)

        return self.d.default_prefix

    def get_language(self, ctx: commands.Context) -> ClassyDict:
        if ctx.guild:
            return self.l[self.language_cache.get(ctx.guild.id, "en")]

        return self.l["en"]

    async def check_global(self, ctx):
        ctx.l = self.get_language(ctx)
        command = ctx.command.name

        if ctx.author.id in self.ban_cache:
            ctx.failure_reason = "bot_banned"
            return False

        if not self.is_ready():
            ctx.failure_reason = "not_ready"
            return False

        if ctx.guild is not None and command in self.disabled_commands.get(ctx.guild.id, ()):
            ctx.failure_reason = "disabled"
            return False

        if command in self.d.sus_commands:
            # implement mob spawning here in the future
            pass

        # handle cooldowns that need to be synced between shard groups / processes
        if command in self.d.cooldown_rates:
            cooldown_info = await self.ipc.request({"type": "cooldown", "command": command, "user_id": ctx.author.id})

            if not cooldown_info.can_run:
                ctx.custom_error = CommandOnCooldown2(cooldown_info.remaining)
                return False

        return True
