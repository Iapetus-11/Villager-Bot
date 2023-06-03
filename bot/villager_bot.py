import asyncio
import random
from collections import defaultdict
from typing import Any, Optional

import aiohttp
import arrow
import captcha.image
import discord
import psutil
from captcha.image import ImageCaptcha
from discord.ext import commands

from common.coms.packet import PACKET_DATA_TYPES
from common.coms.packet_handling import PacketHandlerRegistry, handle_packet
from common.coms.packet_type import PacketType
from common.models.data import Data
from common.models.system_stats import SystemStats
from common.models.topgg_vote import TopggVote
from common.utils.code import execute_code
from common.utils.font_handler import FontHandler
from common.utils.setup import load_data, setup_logging

from bot.models.fwd_dm import ForwardedDirectMessage
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
from bot.utils.setup import load_translations, villager_bot_intents


class VillagerBotCluster(commands.AutoShardedBot, PacketHandlerRegistry):
    def __init__(
        self,
        secrets: Secrets,
        data: Data,
        translations: dict[str, Translation],
    ):
        commands.AutoShardedBot.__init__(
            self,
            command_prefix=secrets.default_prefix,
            case_insensitive=True,
            intents=villager_bot_intents(),
            help_command=None,
        )

        self.cluster_id: Optional[int] = None

        self.start_time = arrow.utcnow()

        self.k = secrets
        self.d = data
        self.l = translations

        self.cog_list = [
            "core.database",
            "core.events",
            "core.loops",
            "core.paginator",
            "core.badges",
            "core.mobs",
            "core.voting",
            "commands.owner",
            "commands.useful",
            "commands.config",
            "commands.econ",
            "commands.minecraft",
            "commands.mod",
            "commands.fun",
        ]

        self.logger = setup_logging("bot", secrets.logging)
        self.karen: Optional[KarenClient] = None
        self.db: Optional[DatabaseProxy] = None
        self.aiohttp: Optional[aiohttp.ClientSession] = None

        # caches
        self.botban_cache = set[int]()  # set({user_id, user_id,..})
        self.language_cache = dict[int, str]()  # {guild_id: "lang"}
        self.prefix_cache = dict[int, str]()  # {guild_id: "prefix"}
        self.disabled_commands = defaultdict[int, set[str]](
            set
        )  # {guild_id: set({command, command,..})}
        self.replies_cache = set[int]()  # {guild_id, guild_id,..}
        self.rcon_cache = dict[tuple[int, Any], Any]()  # {(user_id, mc_server): rcon_client}
        self.existing_users_cache = set[
            int
        ]()  # so the database doesn't have to make a query every time an econ command is ran to ensure user exists
        self.existing_user_lbs_cache = set[
            int
        ]()  # for same reason above, but for leaderboards instead

        self.support_server: Optional[discord.Guild] = None
        self.error_channel: Optional[discord.TextChannel] = None
        self.vote_channel: Optional[discord.TextChannel] = None

        # counters and other things
        self.command_count = 0
        self.message_count = 0
        self.error_count = 0
        self.session_votes = 0
        self.font_files = list[str]()
        self.captcha_generator: ImageCaptcha | None = None

        self.final_ready = asyncio.Event()

        self.add_check(self.check_global)  # register global check
        self.before_invoke(
            self.before_command_invoked
        )  # register self.before_command_invoked as a before_invoked event
        self.after_invoke(
            self.after_command_invoked
        )  # register self.after_command_invoked as a after_invoked event
        self.event(self.on_app_command_completion)

    @property
    def embed_color(self) -> discord.Color:
        return getattr(discord.Color, self.d.embed_color)()

    async def start(self):
        self.font_files = await FontHandler(
            font_urls=self.d.font_urls, output_directory="fonts"
        ).retrieve()
        self.captcha_generator = captcha.image.ImageCaptcha(fonts=self.font_files)

        self.karen = KarenClient(self.k.karen, self.get_packet_handlers(), self.logger)
        self.db = DatabaseProxy(self.karen)

        await self.karen.connect()

        cluster_info = await self.karen.fetch_cluster_init_info()
        self.shard_count = cluster_info.shard_count
        self.shard_ids = cluster_info.shard_ids
        self.cluster_id = cluster_info.cluster_id

        self.aiohttp = aiohttp.ClientSession()

        for cog in self.cog_list:
            await self.load_extension(f"bot.cogs.{cog}")

        await super().start(self.k.discord_token)

    async def close(self, *args, **kwargs):
        if self.karen is not None:
            await self.karen.disconnect()

        if self.aiohttp is not None:
            await self.aiohttp.close()
            self.logger.info("Closed aiohttp ClientSession")

        await super().close(*args, **kwargs)

    async def get_prefix(self, message: discord.Message) -> str:
        if message.guild:
            return self.prefix_cache.get(message.guild.id, self.k.default_prefix)

        return self.k.default_prefix

    def get_language(self, ctx: CustomContext) -> Translation:
        if ctx.guild:
            return self.l[self.language_cache.get(ctx.guild.id, "en")]

        return self.l["en"]

    async def on_ready(self):
        if self.cluster_id == 0:
            try:
                self.logger.info("Syncing slash commands...")

                self.tree.copy_global_to(guild=await self.fetch_guild(self.k.support_server_id))
                await self.tree.sync()

                self.logger.info("Slash commands synced!")
            except Exception:
                self.logger.error(
                    "An error occurred in on_ready while syncing slash commands", exc_info=True
                )

            try:
                self.logger.info("Syncing db item prices...")

                item_prices = {
                    v.db_entry.item: v.db_entry.sell_price for k, v in self.d.shop_items.items()
                }
                item_prices.update(
                    {
                        self.d.farming.name_map[k]: v
                        for k, v in self.d.farming.emerald_yields.items()
                    }
                )
                item_prices.update({f.item: f.sell_price for f in self.d.fishing_findables})

                await self.get_cog("Database").sync_item_prices(item_prices)

                self.logger.info("Done syncing db item prices!")
            except Exception:
                self.logger.error(
                    "An error occurred in on_ready while syncing db item prices", exc_info=True
                )

    async def get_context(self, *args, **kwargs) -> CustomContext:
        ctx = await super().get_context(*args, **kwargs, cls=CustomContext)

        ctx.embed_color = self.embed_color
        ctx.l = self.get_language(ctx)

        return ctx

    async def send_embed(self, location, message: str, *, ignore_exceptions: bool = False) -> None:
        embed = discord.Embed(color=self.embed_color, description=message)

        try:
            await location.send(embed=embed)
        except discord.errors.HTTPException:
            if not ignore_exceptions:
                raise

    async def reply_embed(
        self, location, message: str, ping: bool = False, *, ignore_exceptions: bool = False
    ) -> None:
        embed = discord.Embed(color=self.embed_color, description=message)

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
        command_name = ctx.command.qualified_name

        if ctx.author.id in self.botban_cache:
            ctx.failure_reason = "bot_banned"
            return False

        if not self.is_ready():
            ctx.failure_reason = "not_ready"
            return False

        if ctx.guild is not None and command_name in self.disabled_commands.get(ctx.guild.id, ()):
            ctx.failure_reason = "disabled"
            return False

        # handle cooldowns that need to be synced between shard groups / processes (aka karen cooldowns)
        if command_name in self.d.cooldown_rates:
            cooldown_info = await self.karen.cooldown(command_name, ctx.author.id)

            if not cooldown_info.can_run:
                ctx.custom_error = CommandOnKarenCooldown(cooldown_info.remaining)
                return False

        if command_name in self.d.concurrency_limited:
            if not await self.karen.check_concurrency(command_name, ctx.author.id):
                ctx.custom_error = MaxKarenConcurrencyReached()
                return False

        if ctx.command.cog_name == "Econ":
            # check if user has paused econ
            if await self.karen.check_econ_paused(ctx.author.id):
                ctx.failure_reason = "econ_paused"
                return False

        return True

    async def before_command_invoked(self, ctx: CustomContext):
        self.command_count += 1

        if ctx.command.cog_name == "Econ":
            # random chance to spawn mob
            if random.randint(0, self.d.mob_chance) == 0:
                if self.d.cooldown_rates.get(ctx.command.qualified_name, 0) >= 2:
                    asyncio.create_task(self.get_cog("MobSpawner").spawn_event(ctx))
            elif random.randint(0, self.d.tip_chance) == 0:  # random chance to send tip
                asyncio.create_task(self.send_tip(ctx))

        try:
            if ctx.command.qualified_name in self.d.concurrency_limited:
                await self.karen.acquire_concurrency(ctx.command.qualified_name, ctx.author.id)
        except Exception:
            self.logger.error(
                "An error occurred while attempting to acquire a concurrency lock for command %s for user %s",
                ctx.command,
                ctx.author.id,
                exc_info=True,
            )
            raise

        if ctx.command.qualified_name in self.d.cooldown_rates:
            await self.karen.lb_command_ran(ctx.author.id)

        await self.karen.command_execution(
            ctx.author.id, getattr(ctx.guild, "id", None), ctx.command.qualified_name, False
        )

    async def after_command_invoked(self, ctx: CustomContext):
        try:
            if ctx.command.qualified_name in self.d.concurrency_limited:
                await self.karen.release_concurrency(ctx.command.qualified_name, ctx.author.id)
        except Exception:
            self.logger.error(
                "An error occurred while attempting to release a concurrency lock for command %s for user %s",
                ctx.command,
                ctx.author.id,
                exc_info=True,
            )
            raise

    async def on_app_command_completion(
        self,
        inter: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ):
        if isinstance(command, discord.app_commands.Command):
            await self.karen.command_execution(
                inter.user.id, inter.guild_id, command.qualified_name, True
            )

    ###### packet handlers #####################################################

    @handle_packet(PacketType.EXEC_CODE)
    async def packet_exec_code(self, code: str):
        result = await execute_code(
            code,
            {"bot": self, "db": self.db, "dbc": self.get_cog("Database"), "http": self.aiohttp},
        )

        if not isinstance(result, PACKET_DATA_TYPES):
            result = repr(result)

        return result

    @handle_packet(PacketType.REMINDER)
    async def packet_reminder(self, channel_id: int, user_id: int, message_id: int, reminder: str):
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

    @handle_packet(PacketType.FETCH_BOT_STATS)
    async def packet_fetch_bot_stats(self):
        return [
            len(self.guilds),
            len(self.users),
            self.message_count,
            self.command_count,
            self.latency,
            len(self.private_channels),
            self.session_votes,
        ]

    @handle_packet(PacketType.FETCH_SYSTEM_STATS)
    async def packet_fetch_system_stats(self):
        memory_info = psutil.virtual_memory()

        return SystemStats(
            identifier=f'Cluster {self.cluster_id} ({",".join(map(str, self.shard_ids))})',
            cpu_usage_percent=psutil.getloadavg()[0],
            memory_usage_bytes=(memory_info.total - memory_info.available),
            memory_max_bytes=memory_info.total,
            threads=psutil.Process().num_threads(),
            asyncio_tasks=len(asyncio.all_tasks()),
            start_time=self.start_time.datetime,
        )

    @handle_packet(PacketType.FETCH_GUILD_COUNT)
    async def packet_fetch_guild_count(self):
        return len(self.guilds)

    @handle_packet(PacketType.UPDATE_SUPPORT_SERVER_ROLES)
    async def packet_update_support_server_roles(self, user_id: int):
        support_guild = self.get_guild(self.k.support_server_id)

        if support_guild is not None:
            member = support_guild.get_member(user_id)

            if member is not None:
                await update_support_member_role(self, member)

    @handle_packet(PacketType.RELOAD_DATA)
    async def packet_reload_data(self):
        self.d = load_data()
        self.l = load_translations(self.d.disabled_translations)

    @handle_packet(PacketType.GET_USER_NAME)
    async def packet_get_user_name(self, user_id: int) -> Optional[str]:
        return getattr(self.get_user(user_id), "name", None)

    @handle_packet(PacketType.DM_MESSAGE)
    async def packet_dm_message(
        self, user_id: int, channel_id: int, message_id: int, content: Optional[str]
    ):
        self.dispatch(
            "fwd_dm",
            ForwardedDirectMessage(
                user_id=user_id,
                channel_id=channel_id,
                message_id=message_id,
                content=content,
            ),
        )

    @handle_packet(PacketType.RELOAD_COG)
    async def packet_reload_cog(self, cog: str):
        await self.reload_extension(cog)

    @handle_packet(PacketType.BOTBAN_CACHE_ADD)
    async def packet_botban_cache_add(self, user_id: int):
        self.botban_cache.add(user_id)

    @handle_packet(PacketType.BOTBAN_CACHE_REMOVE)
    async def packet_botban_cache_remove(self, user_id: int):
        try:
            self.botban_cache.remove(user_id)
        except KeyError:
            pass

    @handle_packet(PacketType.LOOKUP_USER)
    async def packet_lookup_user(self, user_id: int):
        member_matches = list[list[int, str]]()

        for guild in self.guilds:
            if guild.get_member(user_id) is not None:
                member_matches.append([guild.id, guild.name])

        return member_matches

    @handle_packet(PacketType.PING)
    async def packet_ping(self):
        return 1

    @handle_packet(PacketType.FETCH_GUILD_IDS)
    async def packet_fetch_guild_ids(self):
        await self.wait_until_ready()
        return [g.id for g in self.guilds]

    @handle_packet(PacketType.SHUTDOWN)
    async def packet_shutdown(self):
        await self.close()

    @handle_packet(PacketType.TOPGG_VOTE)
    async def packet_topgg_vote(self, vote: TopggVote):
        if 0 in self.shard_ids:
            self.dispatch("topgg_vote", vote)

    @handle_packet(PacketType.FETCH_TOP_GUILDS_BY_MEMBERS)
    async def packet_fetch_top_guilds_by_members(self):
        return [
            {"id": g.id, "name": g.name, "count": g.member_count}
            for g in sorted(self.guilds, key=(lambda g: g.member_count), reverse=True)[:10]
        ]

    @handle_packet(PacketType.FETCH_TOP_GUILDS_BY_ACTIVE_MEMBERS)
    async def packet_fetch_top_guilds_by_active_members(self):
        return [
            {**v, "name": self.get_guild(v["id"]).name}
            for v in (await self.get_cog("Database").fetch_guilds_active_count())
        ]

    @handle_packet(PacketType.FETCH_TOP_GUILDS_BY_COMMANDS)
    async def packet_fetch_top_guilds_by_commands(self):
        return [
            {**v, "name": self.get_guild(v["id"]).name}
            for v in (await self.get_cog("Database").fetch_guilds_commands_count())
        ]
