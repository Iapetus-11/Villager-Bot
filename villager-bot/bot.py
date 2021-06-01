from concurrent.futures import ThreadPoolExecutor
from classyjson import ClassyDict
from discord.ext import commands
import aiohttp
import asyncio
import discord
import random
import arrow

from util.setup import villager_bot_intents, setup_logging, setup_database
from util.setup import load_text, load_secrets, load_data
from util.cooldowns import CommandOnKarenCooldown
from util.code import execute_code
from util.ipc import Client


def run_shard_group(shard_count: int, shard_ids: list) -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())

    shard_group = VillagerBotShardGroup(shard_count, shard_ids)

    try:
        shard_group.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        shard_group.logger.error(e)


class VillagerBotShardGroup(commands.AutoShardedBot):
    def __init__(self, shard_count: int, shard_ids: list) -> None:
        super().__init__(
            command_prefix=self.get_prefix,
            intents=villager_bot_intents(),
            shard_count=shard_count,
            shard_ids=shard_ids,
            help_command=None,
        )

        self.start_time = arrow.utcnow()

        self.k = load_secrets()
        self.d = load_data()
        self.l = load_text()

        self.cog_list = [
            "cogs.core.database",
            "cogs.core.events",
            "cogs.core.loops",
            "cogs.commands.owner",
            "cogs.commands.useful",
            "cogs.commands.mod",
            "cogs.commands.fun",
            "cogs.commands.config",
            "cogs.commands.minecraft",
        ]

        self.logger = setup_logging(self.shard_ids)
        self.ipc = Client(self.k.manager.host, self.k.manager.port, self.handle_broadcast)  # ipc client
        self.aiohttp = aiohttp.ClientSession()
        self.db = None  # asyncpg database connection pool
        self.tp = None  # ThreadPoolExecutor instance

        # caches
        self.ban_cache = set()  # {user_id, user_id,..}
        self.language_cache = {}  # {guild_id: "lang"}
        self.prefix_cache = {}  # {guild_id: "prefix"}
        self.disabled_commands = {}  # {guild_id: {command, command,..}}
        self.replies_cache = set()  # {guild_id, guild_id,..}
        self.rcon_cache = {}  # {(user_id, mc_server): rcon_client}

        # support server channels
        self.error_channel = None
        # self.dm_log_channel = None

        # counters and other things
        self.command_count = 0
        self.message_count = 0
        self.error_count = 0
        self.session_votes = 0
        self.spawn_queue = set()  # {ctx, ctx,..}
        self.minecraft_servers = set()  # used for storing servers from minecraft.global {("server:port", server_id)}

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
        with ThreadPoolExecutor() as self.tp:
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

    async def get_prefix(self, ctx: commands.Context) -> str:
        # for some reason discord.py wants this function to be async *sigh*

        if ctx.guild:
            return self.prefix_cache.get(ctx.guild.id, self.d.default_prefix)

        return self.d.default_prefix

    def get_language(self, ctx: commands.Context) -> ClassyDict:
        if ctx.guild:
            return self.l[self.language_cache.get(ctx.guild.id, "en")]

        return self.l["en"]

    async def fetch_error_channel(self):  # needed to log errors from multiple shard groups
        if self.error_channel is None:
            self.error_channel = await self.fetch_channel(self.d.error_channel_id)

        return self.error_channel

    async def send_embed(self, location, message: str) -> None:
        await location.send(embed=discord.Embed(color=self.d.cc, description=message))

    async def reply_embed(self, location, message: str, ping: bool = False) -> None:
        if hasattr(location, "reply"):
            await location.reply(embed=discord.Embed(color=self.d.cc, description=message), mention_author=ping)
        else:
            await self.send_embed(location, message)

    async def send_tip(self, ctx) -> None:
        await asyncio.sleep(random.randint(100, 200) / 100)
        await self.send_embed(ctx, f"{random.choice(ctx.l.misc.tip_intros)} {random.choice(ctx.l.misc.tips)}")

    async def check_global(self, ctx):
        self.command_count += 1

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

        # handle cooldowns that need to be synced between shard groups / processes (aka karen cooldowns)
        if command in self.d.cooldown_rates:
            cooldown_info = await self.ipc.request({"type": "cooldown", "command": command, "user_id": ctx.author.id})

            if not cooldown_info.can_run:
                ctx.custom_error = CommandOnKarenCooldown(cooldown_info.remaining)
                return False

        # handle paused econ users
        if ctx.command.cog_name == "Econ":
            # check if user has paused econ
            res = await self.ipc.eval(f"econ_paused_users.get({ctx.author.id})")

            if res.result is not None:
                ctx.failure_reason = "econ_paused"
                return False

            if random.randint(0, self.d.mob_chance) == 0:  # spawn mob?
                if self.d.cooldown_rates.get(command, 0) >= 2:
                    self.spawn_queue.add(ctx)
            elif random.randint(0, self.d.tip_chance) == 0:  # send tip?
                asyncio.create_task(self.send_tip(ctx))

        return True
