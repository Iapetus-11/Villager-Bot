import asyncio
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

import aiohttp
import arrow
import discord
import psutil
from discord.ext import commands

from common.coms.packet import T_PACKET_DATA
from common.coms.packet_handling import PacketHandlerRegistry, handle_packet
from common.coms.packet_type import PacketType
from common.models.data import Data
from common.utils.code import execute_code
from common.utils.setup import load_data, setup_database_pool

from bot.models.secrets import Secrets
from bot.models.translation import Translation
from bot.utils.ctx import CustomContext
from bot.utils.database_proxy import DatabaseProxy
from bot.utils.karen_client import KarenClient
from bot.utils.misc import (
    CommandOnKarenCooldown,
    MaxKarenConcurrencyReached,
    update_support_member_role,
)
from bot.utils.setup import load_translations, setup_logging, villager_bot_intents


class VillagerBotCluster(commands.AutoShardedBot, PacketHandlerRegistry):
    def __init__(
        self,
        cluster_id: int,
        tp: ThreadPoolExecutor,
        secrets: Secrets,
        data: Data,
        translations: dict[str, Translation],
    ):
        commands.AutoShardedBot.__init__(
            self,
            case_insensitive=True,
            intents=villager_bot_intents(),
            help_command=None,
        )

        self.cluster_id = cluster_id

        self.start_time = arrow.utcnow()

        self.k = secrets
        self.d = data
        self.l = translations

        self.cog_list = [
            "cogs.core.database",
            "cogs.core.events",
            "cogs.core.loops",
            "cogs.core.paginator",
            "cogs.core.badges",
            "cogs.core.mobs",
            "cogs.commands.owner",
            "cogs.commands.useful",
            "cogs.commands.config",
            "cogs.commands.econ",
            "cogs.commands.minecraft",
            "cogs.commands.mod",
            "cogs.commands.fun",
        ]

        self.logger = setup_logging(self.cluster_id)

        self.karen: Optional[KarenClient] = None
        self.aiohttp: Optional[aiohttp.ClientSession] = None
        self.db: Optional[DatabaseProxy] = None
        self.tp = tp

        # caches
        self.ban_cache = set[int]()  # set({user_id, user_id,..})
        self.language_cache = dict[int, str]()  # {guild_id: "lang"}
        self.prefix_cache = dict[int, str]()  # {guild_id: "prefix"}
        self.disabled_commands = defaultdict[int, set[str]](
            set
        )  # {guild_id: set({command, command,..})}
        self.replies_cache = set[int]()  # {guild_id, guild_id,..}
        self.rcon_cache = dict[tuple[int, Any], Any]()  # {(user_id, mc_server): rcon_client}
        self.new_member_cache = defaultdict[int, set](set)  # {guild_id: set()}
        self.existing_users_cache = set[
            int
        ]()  # so the database doesn't have to make a query every time an econ command is ran to ensure user exists
        self.existing_user_lbs_cache = set[
            int
        ]()  # for same reason above, but for leaderboards instead

        # support server channels
        self.error_channel: Optional[discord.TextChannel] = None
        self.vote_channel: Optional[discord.TextChannel] = None

        # counters and other things
        self.command_count = 0
        self.message_count = 0
        self.error_count = 0
        self.session_votes = 0

        self.add_check(self.check_global)  # register global check
        self.before_invoke(
            self.before_command_invoked
        )  # register self.before_command_invoked as a before_invoked event
        self.after_invoke(
            self.after_command_invoked
        )  # register self.after_command_invoked as a after_invoked event

    async def start(self):
        self.karen = KarenClient(self.k.karen, self.get_packet_handlers(), self.logger)
        self.db = DatabaseProxy(self.karen)

        self.shard_ids = await self.karen.fetch_shard_ids()
        self.shard_count = len(self.shard_ids)

        for cog in self.cog_list:
            self.load_extension(cog)

        await super().start(self.k.discord_token)

    async def close(self, *args, **kwargs):
        await self.karen.disconnect()
        await self.aiohttp.close()

        await super().close(*args, **kwargs)

    async def get_prefix(self, message: discord.Message) -> str:
        # for some reason discord.py wants this function to be async

        if message.guild:
            return self.prefix_cache.get(message.guild.id, self.k.default_prefix)

        return self.k.default_prefix

    def get_language(self, ctx: CustomContext) -> Translation:
        if ctx.guild:
            return self.l[self.language_cache.get(ctx.guild.id, "en")]

        return self.l["en"]

    async def get_context(self, *args, **kwargs) -> CustomContext:
        ctx = await super().get_context(*args, **kwargs, cls=CustomContext)

        ctx.embed_color = self.d.embed_color
        ctx.l = self.get_language(ctx)

        return ctx

    async def send_embed(self, location, message: str, *, ignore_exceptions: bool = False) -> None:
        embed = discord.Embed(color=self.d.cc, description=message)

        try:
            await location.send(embed=embed)
        except discord.errors.HTTPException:
            if not ignore_exceptions:
                raise

    async def reply_embed(
        self, location, message: str, ping: bool = False, *, ignore_exceptions: bool = False
    ) -> None:
        embed = discord.Embed(color=self.d.cc, description=message)

        try:
            await location.reply(embed=embed, mention_author=ping)
        except discord.errors.HTTPException as e:
            if (
                e.code == 50035
            ):  # invalid form body, happens sometimes when the message to reply to can't be found?
                await self.send_embed(location, message, ignore_exceptions=ignore_exceptions)
            elif not ignore_exceptions:
                raise

    async def send_tip(self, ctx: CustomContext) -> None:
        await asyncio.sleep(random.randint(100, 200) / 100)
        await self.send_embed(
            ctx, f"{random.choice(ctx.l.misc.tip_intros)} {random.choice(ctx.l.misc.tips)}"
        )

    async def check_global(self, ctx: CustomContext) -> bool:  # the global command check
        self.command_count += 1

        command = str(ctx.command)

        if ctx.author.id in self.ban_cache:
            ctx.failure_reason = "bot_banned"
            return False

        if not self.is_ready():
            ctx.failure_reason = "not_ready"
            return False

        if ctx.guild is not None and command in self.disabled_commands.get(ctx.guild.id, ()):
            ctx.failure_reason = "disabled"
            return False

        command_has_cooldown = command in self.d.cooldown_rates

        # handle cooldowns that need to be synced between shard groups / processes (aka karen cooldowns)
        if command_has_cooldown:
            cooldown_info = await self.karen.cooldown(command, ctx.author.id)

            if not cooldown_info.can_run:
                ctx.custom_error = CommandOnKarenCooldown(cooldown_info.remaining)
                return False

        if command in self.d.concurrency_limited:
            if not await self.karen.check_concurrency(command, ctx.author.id):
                ctx.custom_error = MaxKarenConcurrencyReached()
                return False

        if ctx.command.cog_name == "Econ":
            # check if user has paused econ
            if await self.karen.check_econ_paused(ctx.author.id):
                ctx.failure_reason = "econ_paused"
                return False

            # random chance to spawn mob
            if random.randint(0, self.d.mob_chance) == 0:
                if self.d.cooldown_rates.get(command, 0) >= 2:
                    if not self.prevent_spawn_duplicates.check(ctx.channel.id):
                        self.prevent_spawn_duplicates.put(ctx.channel.id)
                        asyncio.create_task(self.get_cog("MobSpawner").spawn_event(ctx))
            elif random.randint(0, self.d.tip_chance) == 0:  # random chance to send tip
                asyncio.create_task(self.send_tip(ctx))

        if command_has_cooldown:
            asyncio.create_task(
                self.ipc.send({"type": PacketType.COMMAND_RAN, "user_id": ctx.author.id})
            )

        return True

    async def before_command_invoked(self, ctx: CustomContext):
        try:
            if str(ctx.command) in self.d.concurrency_limited:
                await self.ipc.send(
                    {
                        "type": PacketType.CONCURRENCY_ACQUIRE,
                        "command": str(ctx.command),
                        "user_id": ctx.author.id,
                    }
                )
        except Exception:
            self.logger.error(
                "An error occurred while attempting to acquire a concurrency lock for command %s for user %s",
                ctx.command,
                ctx.author.id,
                exc_info=True,
            )
            raise

    async def after_command_invoked(self, ctx: CustomContext):
        try:
            if str(ctx.command) in self.d.concurrency_limited:
                await self.ipc.send(
                    {
                        "type": PacketType.CONCURRENCY_RELEASE,
                        "command": str(ctx.command),
                        "user_id": ctx.author.id,
                    }
                )
        except Exception:
            self.logger.error(
                "An error occurred while attempting to release a concurrency lock for command %s for user %s",
                ctx.command,
                ctx.author.id,
                exc_info=True,
            )
            raise

    ###### packet handlers #####################################################

    @handle_packet(PacketType.EXEC_CODE)
    async def handle_exec_packet(self, code: str):
        result = await execute_code(
            code,
            {"bot": self, "db": self.db, "dbc": self.get_cog("Database"), "http": self.aiohttp},
        )

        if not isinstance(result, T_PACKET_DATA):
            result = repr(result)

        return result

    @handle_packet(PacketType.REMINDER)
    async def handle_reminder_packet(
        self, channel_id: int, user_id: int, message_id: int, reminder: str
    ):
        success = False
        channel = self.get_channel(channel_id)

        if channel is not None:
            user = self.get_user(user_id)

            if user is not None:
                lang = self.get_language(channel)

                try:
                    message = await channel.fetch_message(message_id)
                    await message.reply(
                        lang.useful.remind.reminder.format(user.mention, reminder),
                        mention_author=True,
                    )
                    success = True
                except Exception:
                    try:
                        await channel.send(
                            lang.useful.remind.reminder.format(user.mention, reminder)
                        )
                        success = True
                    except Exception:
                        self.logger.error(
                            "An error occurred while sending a reminder", exc_info=True
                        )

        return {"success": success}

    @handle_packet(PacketType.FETCH_STATS)
    async def handle_fetch_stats_packet(self):
        proc = psutil.Process()
        with proc.oneshot():
            mem_usage = proc.memory_full_info().uss
            threads = proc.num_threads()

        return {
            "stats": [
                mem_usage,
                threads,
                len(asyncio.all_tasks()),
                len(self.guilds),
                len(self.users),
                self.message_count,
                self.command_count,
                self.latency,
                len(self.private_channels),
                self.session_votes,
            ],
        }

    @handle_packet(PacketType.UPDATE_SUPPORT_SERVER_ROLES)
    async def handle_update_support_server_roles_packet(self, user_id: int):
        support_guild = self.get_guild(self.d.support_server_id)

        if support_guild is not None:
            member = support_guild.get_member(user_id)

            if member is not None:
                await update_support_member_role(self, member)

    @handle_packet(PacketType.RELOAD_DATA)
    async def handle_reload_data_packet(self):
        self.l = load_translations()
        self.d = load_data()

    @handle_packet(PacketType.GET_USER_NAME)
    async def handle_get_user_name(self, user_id: int) -> Optional[str]:
        return getattr(self.get_user(user_id), "name", None)
