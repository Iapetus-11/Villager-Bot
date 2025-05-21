import asyncio
import itertools
import random
from datetime import datetime, timezone
from typing import Any

import aiohttp
from bot.logic.command_errors import BotNotReadyYet, CommandDisabledByGuild, UserBotBanned
import captcha.image
import discord
import psutil
from captcha.image import ImageCaptcha
from discord.ext import commands

from bot.logic.ctx import CustomContext
from bot.logic.errors import CommandOnKarenCooldownError
from bot.logic.home_guild import (
    update_support_member_role,
)
from bot.logic.setup import load_data, load_translations, setup_logging, villager_bot_intents
from bot.models.data import Data
from bot.models.fwd_dm import ForwardedDirectMessage
from bot.models.secrets import Secrets
from bot.models.translation import Translation
from bot.services.karen import KarenClient
from bot.services.karen.resources.command_executions import (
    CommandExecutionPreflightCommandOnCooldownError,
    CommandExecutionPreflightRequest,
    CommandExecutionPreflightSuccess,
)
from bot.utils.code import execute_code
from bot.utils.font_handler import FontHandler


class VillagerBotCluster(commands.AutoShardedBot):
    def __init__(
        self,
        cluster_id: int,
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

        self.start_time = datetime.now(timezone.utc)

        self.cluster_id = cluster_id
        self.shard_ids = list(
            list(itertools.batched(range(secrets.total_shard_count), secrets.total_cluster_count))[cluster_id]
        )
        self.shard_count = secrets.total_shard_count

        self.k = secrets
        self.d = data
        self.l = translations

        self.owner_id = self.k.owner_id
        self.owner_ids = {self.k.owner_id}

        self.cog_list = [
            "core.database",
            "core.events",
            "core.loops",
            "core.paginator",
            "core.badges",
            "core.quests",
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
        self.karen: KarenClient = KarenClient(secrets.karen.base_url, secrets.karen.api_key)
        self.aiohttp: aiohttp.ClientSession | None = None

        # caches
        self.rcon_cache: dict[tuple[int, Any], Any] = {}  # {(user_id, mc_server): rcon_client}  # TODO: Revisit types

        self.support_server: discord.Guild | None = None
        self.error_channel: discord.TextChannel | None = None
        self.vote_channel: discord.TextChannel | None = None

        # counters and other things
        self.font_files = list[str]()
        self.captcha_generator: ImageCaptcha | None = None

        self.final_ready = asyncio.Event()

        self.add_check(self.check_global)  # register global check

    @property
    def embed_color(self) -> discord.Color:
        return getattr(discord.Color, self.d.embed_color)()

    async def start(self):  # type: ignore[override]
        self.font_files = await FontHandler(
            font_urls=self.d.font_urls,
            output_directory="fonts",
        ).retrieve()
        self.captcha_generator = captcha.image.ImageCaptcha(fonts=self.font_files)

        self.aiohttp = aiohttp.ClientSession()

        for cog in self.cog_list:
            await self.load_extension(f"bot.cogs.{cog}")

        await super().start(self.k.discord_token)

    async def close(self, *args, **kwargs):
        if self.karen is not None:
            await self.karen.close()

        if self.aiohttp is not None:
            await self.aiohttp.close()
            self.logger.info("Closed aiohttp ClientSession")

        await super().close(*args, **kwargs)

    async def get_prefix(self, message: discord.Message) -> str:
        if message.guild:
            guild_settings = await self.karen.discord.cached.guilds.get(message.guild.id)
            return guild_settings.prefix

        return self.k.default_prefix

    async def get_language(self, ctx: CustomContext) -> Translation:
        if ctx.guild:
            guild_settings = await self.karen.discord.cached.guilds.get(ctx.guild.id)
            return self.l[guild_settings.language]

        return self.l["en"]

    async def on_ready(self):
        if self.cluster_id == 0:
            try:
                self.logger.info("Syncing slash commands...")

                self.tree.copy_global_to(guild=await self.fetch_guild(self.k.support_server_id))
                await self.tree.sync()

                self.logger.info("Slash commands synced!")
            except Exception:
                self.logger.exception(
                    "An error occurred in on_ready while syncing slash commands",
                )

            # try:
            #     self.logger.info("Syncing db item prices...")

            #     item_prices = {v.db_entry.item: v.db_entry.sell_price for k, v in self.d.shop_items.items()}
            #     item_prices.update(
            #         {self.d.farming.name_map[k]: v for k, v in self.d.farming.emerald_yields.items()},
            #     )
            #     item_prices.update({f.item: f.sell_price for f in self.d.fishing_findables})
            #     item_prices.update({
            #         self.d.farming.name_map[crop_type]: emerald_amount
            #         for crop_type, emerald_amount in self.d.farming.emerald_yields.items()
            #     })

            #     await self.get_cog("Database").sync_item_prices(item_prices)

            #     self.logger.info("Done syncing db item prices!")
            # except Exception:
            #     self.logger.exception(
            #         "An error occurred in on_ready while syncing db item prices",
            #     )

    async def get_context(self, *args, **kwargs) -> CustomContext:  # type: ignore[override]
        ctx: CustomContext = await super().get_context(*args, **kwargs, cls=CustomContext)

        await ctx.async_init()

        return ctx

    async def send_embed(self, location, message: str, *, ignore_exceptions: bool = False) -> None:
        embed = discord.Embed(color=self.embed_color, description=message)

        try:
            await location.send(embed=embed)
        except discord.errors.HTTPException:
            if not ignore_exceptions:
                raise

    async def reply_embed(
        self,
        location,
        message: str,
        ping: bool = False,
        *,
        ignore_exceptions: bool = False,
    ) -> None:
        embed = discord.Embed(color=self.embed_color, description=message)

        try:
            await location.reply(embed=embed, mention_author=ping)
        except discord.errors.HTTPException as e:
            if e.code == 50035:  # invalid form body, happens sometimes when the message to reply to can't be found?
                await self.send_embed(location, message, ignore_exceptions=ignore_exceptions)
            elif not ignore_exceptions:
                raise

    async def send_tip(self, ctx: CustomContext) -> None:
        await asyncio.sleep(random.randint(100, 200) / 100)
        await self.send_embed(
            ctx,
            f"{random.choice(ctx.l.misc.tip_intros)} {random.choice(ctx.l.misc.tips)}",
        )

    async def check_global(self, ctx: CustomContext) -> bool:  # the global command check
        assert ctx.command is not None

        command_name = ctx.command.qualified_name

        karen_user = await self.karen.cached.users.get(ctx.author.id)
        karen_guild_settings = (await self.karen.discord.cached.guilds.get(ctx.guild.id)) if ctx.guild else None

        if karen_user.banned:
            raise UserBotBanned()

        if not self.is_ready():
            raise BotNotReadyYet()

        if karen_guild_settings is not None and command_name in karen_guild_settings.disabled_commands:
            raise CommandDisabledByGuild()

        preflight = await self.karen.command_executions.preflight(
            CommandExecutionPreflightRequest(
                user_id=karen_user.id,
                command=command_name,
                at=datetime.now(timezone.utc),
                discord_guild_id=ctx.guild.id if ctx.guild else None,
            )
        )

        if isinstance(preflight, CommandExecutionPreflightSuccess):  # noqa: SIM102
            if preflight.spawn_mob:
                ...  # TODO: Move this to Karen?
                # asyncio.create_task(self.get_cog("MobSpawner").spawn_event(ctx))
            elif random.randint(0, self.d.tip_chance) == 0:  # random chance to send tip
                asyncio.create_task(self.send_tip(ctx))

        if isinstance(preflight, CommandExecutionPreflightCommandOnCooldownError):
            ctx.custom_error = CommandOnKarenCooldownError(preflight.until)
            return False

        return True

    # packet handlers #####################################################

    async def packet_exec_code(self, code: str):
        result = await execute_code(
            code,
            {"bot": self, "db": self.db, "dbc": self.get_cog("Database"), "http": self.aiohttp},
        )

        if not isinstance(result, PACKET_DATA_TYPES):
            result = repr(result)

        return result

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
                            lang.useful.remind.reminder.format(user.mention, reminder),
                        )
                        success = True
                    except Exception:
                        self.logger.exception("An error occurred while sending a reminder")

        return {"success": success}

    async def packet_fetch_system_stats(self):
        memory_info = psutil.virtual_memory()

        return SystemStats(
            identifier=f"Cluster {self.cluster_id} ({','.join(map(str, self.shard_ids))})",
            cpu_usage_percent=psutil.getloadavg()[0],
            memory_usage_bytes=(memory_info.total - memory_info.available),
            memory_max_bytes=memory_info.total,
            threads=psutil.Process().num_threads(),
            asyncio_tasks=len(asyncio.all_tasks()),
            start_time=self.start_time.datetime,
        )

    async def packet_fetch_guild_count(self):
        return len(self.guilds)

    async def packet_update_support_server_roles(self, user_id: int):
        support_guild = self.get_guild(self.k.support_server_id)

        if support_guild is not None:
            member = support_guild.get_member(user_id)

            if member is not None:
                await update_support_member_role(self, member)

    async def packet_reload_data(self):
        self.d = load_data()
        self.l = load_translations(self.d.disabled_translations)

    async def packet_get_user_name(self, user_id: int) -> str | None:
        return getattr(self.get_user(user_id), "name", None)

    async def packet_dm_message(
        self,
        user_id: int,
        channel_id: int,
        message_id: int,
        content: str | None,
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

    async def packet_reload_cog(self, cog: str):
        await self.reload_extension(cog)

    async def packet_botban_cache_add(self, user_id: int):
        self.botban_cache.add(user_id)

    async def packet_botban_cache_remove(self, user_id: int):
        try:
            self.botban_cache.remove(user_id)
        except KeyError:
            pass

    async def packet_lookup_user(self, user_id: int):
        member_matches = list[list[int, str]]()

        for guild in self.guilds:
            if guild.get_member(user_id) is not None:
                member_matches.append([guild.id, guild.name])

        return member_matches

    async def packet_ping(self):
        return 1

    async def packet_fetch_guild_ids(self):
        await self.wait_until_ready()
        return [g.id for g in self.guilds]

    async def packet_shutdown(self):
        await self.close()

    async def packet_topgg_vote(self, vote):
        if 0 in self.shard_ids:
            self.dispatch("topgg_vote", vote)

    async def packet_fetch_top_guilds_by_members(self):
        return [
            {"id": g.id, "name": g.name, "count": g.member_count}
            for g in sorted(self.guilds, key=(lambda g: g.member_count), reverse=True)[:10]
        ]

    async def packet_fetch_top_guilds_by_active_members(self):
        return [
            {**v, "name": self.get_guild(v["id"]).name}
            for v in (await self.get_cog("Database").fetch_guilds_active_member_count())
        ]

    async def packet_fetch_top_guilds_by_commands(self):
        return [
            {**v, "name": self.get_guild(v["id"]).name}
            for v in (await self.get_cog("Database").fetch_guilds_commands_count_over_30d())
        ]
