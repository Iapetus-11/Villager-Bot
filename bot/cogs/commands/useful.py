import asyncio
import json
import os
import secrets
import time
from contextlib import suppress
from typing import Optional
from urllib.parse import quote as urlquote

import aiofiles
import aiohttp
import arrow
import async_cse
import discord
import moviepy.editor
import psutil
from bot.cogs.core.database import Database
from bot.cogs.core.paginator import Paginator
from discord.ext import commands, tasks

from bot.utils.ctx import Ctx
from bot.utils.misc import SuppressCtxManager, get_timedelta_granularity, parse_timedelta
from bot.villager_bot import VillagerBotCluster


class BanCacheEntry:
    __slots__ = ("ban_count", "time")

    def __init__(self, ban_count: int):
        self.ban_count = ban_count
        self.time = time.time()


class Useful(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d
        self.db: Database = bot.get_cog("Database")
        self.karen = bot.karen
        self.google = async_cse.Search(bot.k.google_search)
        self.aiohttp = bot.aiohttp

        self.ban_count_cache = {}

        self.snipes = {}
        self.clear_snipes.start()

    def cog_unload(self):
        self.clear_snipes.cancel()

    @property
    def paginator(self) -> Paginator:
        return self.bot.get_cog("Paginator")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot and message.content:
            self.snipes[message.channel.id] = message, time.time()

    @tasks.loop(seconds=30)
    async def clear_snipes(self):
        for k, v in list(self.snipes.items()):
            if time.time() - v[1] > 60:
                try:
                    del self.snipes[k]
                except KeyError:
                    pass

    @commands.group(name="help", case_insensitive=True)
    async def help(self, ctx: Ctx):
        if ctx.invoked_subcommand is None:
            cmd = ctx.message.content.replace(f"{ctx.prefix}help ", "")

            if cmd != "":
                cmd_true = self.bot.get_command(cmd.lower())

                if cmd_true is not None:
                    all_help = {
                        **ctx.l.help.econ,
                        **ctx.l.help.mc,
                        **ctx.l.help.util,
                        **ctx.l.help.fun,
                        **ctx.l.help.mod,
                    }

                    help_text = all_help.get(str(cmd_true))

                    if help_text is None:
                        await ctx.reply_embed(ctx.l.help.main.nodoc)
                        return

                    embed = discord.Embed(color=self.bot.embed_color)

                    embed.set_author(name=ctx.l.help.n.cmd, icon_url=self.d.splash_logo)
                    embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

                    embed.description = help_text.format(ctx.prefix)

                    if len(cmd_true.aliases) > 0:
                        embed.description += "\n\n" + ctx.l.help.main.aliases.format(
                            "`, `".join(cmd_true.aliases)
                        )

                    try:
                        await ctx.reply(embed=embed, mention_author=False)
                    except discord.errors.HTTPException as e:
                        if (
                            e.code == 50035
                        ):  # invalid form body, happens sometimes when the message to reply to can't be found?
                            await ctx.send(embed=embed, mention_author=False)
                        else:
                            raise

                    return

            embed = discord.Embed(color=self.bot.embed_color)
            embed.set_author(name=ctx.l.help.n.title, icon_url=self.d.splash_logo)
            embed.description = ctx.l.help.main.desc.format(self.d.support, self.d.topgg)

            p = ctx.prefix

            embed.add_field(
                name=(self.d.emojis.emerald_spinn + ctx.l.help.n.economy), value=f"`{p}help econ`"
            )
            embed.add_field(
                name=(self.d.emojis.bounce + " " + ctx.l.help.n.minecraft), value=f"`{p}help mc`"
            )
            embed.add_field(
                name=(self.d.emojis.anichest + ctx.l.help.n.utility), value=f"`{p}help util`"
            )

            embed.add_field(
                name=(self.d.emojis.rainbow_shep + ctx.l.help.n.fun), value=f"`{p}help fun`"
            )
            embed.add_field(
                name=(self.d.emojis.netherite_sword_ench + ctx.l.help.n.admin),
                value=f"`{p}help admin`",
            )
            embed.add_field(
                name=(self.d.emojis.heart_spin + ctx.l.help.main.support),
                value=f"**[{ctx.l.help.main.clickme}]({self.d.support})**",
            )

            embed.set_footer(
                text=ctx.l.useful.credits.foot.format(ctx.prefix)
                + "  |  "
                + ctx.l.useful.rules.slashrules.format(ctx.prefix)
            )

            await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="economy", aliases=["econ"])
    async def help_economy(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name=f"{ctx.l.help.n.title} [{ctx.l.help.n.economy}]", icon_url=self.d.splash_logo
        )
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.econ))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="minecraft", aliases=["mc"])
    async def help_minecraft(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name=f"{ctx.l.help.n.title} [{ctx.l.help.n.minecraft}]", icon_url=self.d.splash_logo
        )
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.mc))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="utility", aliases=["util", "useful"])
    async def help_utility(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name=f"{ctx.l.help.n.title} [{ctx.l.help.n.utility}]", icon_url=self.d.splash_logo
        )
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.util))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="fun")
    async def help_fun(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name=f"{ctx.l.help.n.title} [{ctx.l.help.n.fun}]", icon_url=self.d.splash_logo
        )
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.fun))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="administrator", aliases=["mod", "moderation", "administrative", "admin"])
    async def help_administrative(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(
            name=f"{ctx.l.help.n.title} [{ctx.l.help.n.admin}]", icon_url=self.d.splash_logo
        )
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.mod))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="credits")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def credits(self, ctx: Ctx):
        embed_template = discord.Embed(color=self.bot.embed_color)
        embed_template.set_author(name=ctx.l.useful.credits.credits, icon_url=self.d.splash_logo)

        fields: list[dict[str, str]] = []

        entry: tuple[int, str]
        for i, entry in enumerate(ctx.l.useful.credits.people.items()):
            user_id, contribution = entry

            # get user's current name
            user = self.bot.get_user(self.d.credit_users[user_id])
            if user is None:
                user = await self.bot.fetch_user(self.d.credit_users[user_id])

            fields.append({"name": f"**{user.display_name}**", "value": contribution})

            if i % 2 == 1:
                fields.append({"value": "\uFEFF", "name": "\uFEFF"})

        pages = [fields[i : i + 9] for i in range(0, len(fields), 9)]
        del fields

        def get_page(page: int) -> discord.Embed:
            embed = embed_template.copy()

            for field in pages[page]:
                embed.add_field(**field)

            embed.set_footer(text=f"{ctx.l.econ.page} {page+1}/{len(pages)}")

            return embed

        await self.paginator.paginate_embed(ctx, get_page, timeout=60, page_count=len(pages))

    @commands.command(name="avatar", aliases=["av"])
    async def member_avatar(self, ctx: Ctx, member: discord.Member = None):
        user = member or ctx.author
        avatar_url = getattr(
            user.avatar,
            "url",
            "https://media.discordapp.net/attachments/643648150778675202/947881629047722064/gGWDJSghKgd8QAAAABJRU5ErkJggg.png",
        )

        embed = discord.Embed(
            color=self.bot.embed_color, description=ctx.l.fun.dl_img.format(avatar_url)
        )
        embed.set_image(url=avatar_url)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="ping", aliases=["pong", "ding", "dong", "bing", "bong", "shing", "shling", "schlong"]
    )
    async def ping_pong(self, ctx: Ctx):
        content = ctx.message.content.lower()

        if "ping" in content:
            pp = "Pong"
        elif "pong" in content:
            pp = "Ping"
        elif "ding" in content:
            pp = "Dong"
        elif "dong" in content:
            pp = "Ding"
        elif "bing" in content:
            pp = "Bong"
        elif "bong" in content:
            pp = "Bing"
        elif "shing" in content or "shling" in content:
            pp = "Schlong"
        elif "schlong" in content:
            await ctx.reply_embed(f"{self.d.emojis.aniheart} Magnum Dong! \uFEFF `69.00 ms`")
            return

        await ctx.reply_embed(
            f"{self.d.emojis.aniheart} {pp}! \uFEFF `{round(self.bot.latency*1000, 2)} ms`"
        )

    @commands.command(name="vote", aliases=["votelink", "votelinks"])
    async def votelinks(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name="Vote for Villager Bot!", icon_url=self.d.splash_logo)

        embed.description = f'**[{ctx.l.useful.vote.click_1}]({self.d.topgg + "/vote"})**'

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="links",
        aliases=["invite", "support", "usefullinks", "website", "source", "privacypolicy"],
    )
    async def useful_links(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(name="Useful Links", icon_url=self.d.splash_logo)

        embed.description = (
            f"**[{ctx.l.useful.links.support}]({self.d.support})\n"
            f"\n[{ctx.l.useful.links.invite}]({self.d.invite})\n"
            f"\n[{ctx.l.useful.links.topgg}]({self.d.topgg})\n"
            f"\n[{ctx.l.useful.links.source}]({self.d.github})\n"
            f"\n[{ctx.l.useful.links.privacy}]({self.d.privacy_policy})**"
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="stats", aliases=["bs"])
    async def stats(self, ctx: Ctx):
        with suppress(Exception):
            await ctx.trigger_typing()

        uptime_seconds = (arrow.utcnow() - self.bot.start_time).total_seconds()
        uptime = (
            arrow.utcnow()
            .shift(seconds=uptime_seconds)
            .humanize(locale=ctx.l.lang, only_distance=True)
        )

        clusters_stats, karen_stats, cluster_ping = await asyncio.gather(
            self.karen.fetch_clusters_stats(),
            self.karen.fetch_karen_stats(),
            self.karen.fetch_clusters_ping(),
        )

        (
            mem_usage,
            threads,
            asyncio_tasks,
            guild_count,
            user_count,
            message_count,
            command_count,
            latency_all,
            dm_count,
            session_votes,
        ) = map(sum, zip(*(clusters_stats + [karen_stats])))

        total_mem = psutil.virtual_memory().total

        embed = discord.Embed(color=self.bot.embed_color)

        embed.set_author(name=ctx.l.useful.stats.stats, icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        col_1 = (
            f"{ctx.l.useful.stats.servers}: `{guild_count}`\n"
            f"{ctx.l.useful.stats.dms}: `{dm_count}`\n"
            f"{ctx.l.useful.stats.users}: `{user_count}`\n"
            f"{ctx.l.useful.stats.msgs}: `{message_count}`\n"
            f"{ctx.l.useful.stats.cmds}: `{command_count}` `({round((command_count / (message_count + .0000001)) * 100, 2)}%)`\n"
            f"{ctx.l.useful.stats.cmds_sec}: `{round(command_count / uptime_seconds, 2)}`\n"
            f"{ctx.l.useful.stats.votes}: `{session_votes}`\n"
            f"{ctx.l.useful.stats.topgg}: `{round((session_votes / uptime_seconds) * 3600, 2)}`\n"
        )

        col_2 = (
            f"{ctx.l.useful.stats.mem}: `{round(mem_usage / 1000000000, 2)} GB` `({round(mem_usage / total_mem * 100, 2)}%)`\n"
            f"{ctx.l.useful.stats.cpu}: `{round(psutil.getloadavg()[0] / psutil.cpu_count() * 100, 2)}%`\n"
            f"{ctx.l.useful.stats.threads}: `{threads}`\n"
            f"{ctx.l.useful.stats.tasks}: `{asyncio_tasks}`\n"
            f"Discord {ctx.l.useful.stats.ping}: `{round((latency_all/len(clusters_stats)) * 1000, 2)} ms`\n"
            f"Cluster {ctx.l.useful.stats.ping}: `{round(cluster_ping * 1000, 2)} ms`\n"
            f"{ctx.l.useful.stats.shards}: `{self.bot.shard_count}`\n"
            f"{ctx.l.useful.stats.uptime}: `{uptime}`\n"
        )

        embed.add_field(name="\uFEFF", value=col_1 + "\uFEFF")
        embed.add_field(name="\uFEFF", value=col_2 + "\uFEFF")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="serverinfo", aliases=["server", "guild", "guildinfo"])
    @commands.guild_only()
    async def server_info(self, ctx: Ctx, *, guild: discord.Guild = None):
        with suppress(Exception):
            await ctx.trigger_typing()

        if guild is None:
            guild = ctx.guild

        db_guild = await self.db.fetch_guild(guild.id)

        age = arrow.get(discord.utils.snowflake_time(guild.id))
        display_age = (
            age.format("MMM D, YYYY", locale=ctx.l.lang) + ", " + age.humanize(locale=ctx.l.lang)
        )

        ban_cache_entry = self.ban_count_cache.get(ctx.guild.id)
        timed_out = False

        if ban_cache_entry is not None:
            if time.time() - ban_cache_entry.time > 60 * 60 * 60:
                ban_cache_entry = None
            else:
                bans = ban_cache_entry.ban_count

        if ban_cache_entry is None:
            try:
                bans = len(await asyncio.wait_for(guild.bans(), 1))
            except asyncio.TimeoutError:  # so many bans, eeee
                bans = "unknown"
                timed_out = True
            except Exception:
                bans = "unknown"

        async def update_ban_count_cache(bans_: int = None):
            if bans_ is None:
                bans_ = len(await guild.bans())

            self.ban_count_cache[ctx.guild.id] = BanCacheEntry(bans_)

        if timed_out:
            asyncio.create_task(update_ban_count_cache())
        elif isinstance(bans, int):
            if bans > 100:
                asyncio.create_task(update_ban_count_cache(bans))

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_author(
            name=f"{guild.name} {ctx.l.useful.ginf.info}",
            icon_url=getattr(guild.icon, "url", None),
        )

        embed.description = f"{ctx.l.useful.ginf.age}: `{display_age}`\n{ctx.l.useful.ginf.owner}: {guild.owner.mention}"

        general = (
            f"{ctx.l.useful.ginf.members}: `{len([m for m in guild.members if not m.bot])}`\n"
            f"{ctx.l.useful.ginf.channels}: `{len(guild.text_channels) + len(guild.voice_channels)}`\n "
            f"{ctx.l.useful.ginf.roles}: `{len(guild.roles)}`\n"
            f"{ctx.l.useful.ginf.emojis}: `{len(guild.emojis)}`\n"
            f"{ctx.l.useful.ginf.bans}: `{bans}`\n"
        )

        villager = (
            f"{ctx.l.useful.ginf.lang}: `{ctx.l.name}`\n"
            f"{ctx.l.useful.ginf.diff}: `{db_guild.difficulty}`\n"
            f"{ctx.l.useful.ginf.cmd_prefix}: `{await self.bot.get_prefix(ctx)}`\n"
        )

        embed.add_field(name="General :gear:", value=general, inline=True)
        embed.add_field(name="Villager Bot " + self.d.emojis.emerald, value=villager, inline=True)
        # embed.add_field(name="Roles", value=" ".join([r.mention for r in guild.roles if r.id != guild.id][::-1]))

        embed.set_thumbnail(url=getattr(guild.icon, "url", None))
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="rules", aliases=["botrules"])
    async def rules(self, ctx: Ctx):
        embed = discord.Embed(color=self.bot.embed_color, description=ctx.l.useful.rules.penalty)

        embed.set_author(name=ctx.l.useful.rules.rules, icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_1.format(self.d.support))
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_2)

        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_3)
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_4)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="math", aliases=["solve", "meth"])
    async def math(self, ctx: Ctx, *, problem):
        async with SuppressCtxManager(ctx.typing()):
            try:
                resp = await self.aiohttp.get(
                    f"https://api.mathjs.org/v4/?expr={urlquote(problem)}"
                )
                await ctx.reply_embed(f"```{float(await resp.text())}```")
            except Exception:
                await ctx.reply_embed(ctx.l.useful.meth.oops)

    @commands.command(name="google", aliases=["thegoogle", "gewgle"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def google_search(self, ctx: Ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with SuppressCtxManager(ctx.typing()):
                res = await self.google.search(query, safesearch=safesearch)
        except async_cse.search.NoResults:
            await ctx.reply_embed(ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await ctx.reply_embed(ctx.l.useful.search.error)
            return

        if len(res) == 0:
            await ctx.reply_embed(ctx.l.useful.search.nope)
            return

        res = res[0]

        embed = discord.Embed(
            color=self.bot.embed_color, title=res.title, description=res.description, url=res.url
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="youtube", aliases=["ytsearch", "yt"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def youtube_search(self, ctx: Ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with SuppressCtxManager(ctx.typing()):
                res = await self.google.search(query, safesearch=safesearch)
        except async_cse.search.NoResults:
            await ctx.reply_embed(ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await ctx.reply_embed(ctx.l.useful.search.error)
            return

        res = tuple(filter((lambda r: "youtube.com/watch" in r.url), res))

        if len(res) == 0:
            await ctx.reply_embed(ctx.l.useful.search.nope)
            return

        res = res[0]

        await ctx.reply(res.url, mention_author=False)

    @commands.command(name="image", aliases=["imagesearch", "img"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def image_search(self, ctx: Ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with SuppressCtxManager(ctx.typing()):
                results = await self.google.search(query, safesearch=safesearch, image_search=True)
        except async_cse.search.NoResults:
            await ctx.reply_embed(ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await ctx.reply_embed(ctx.l.useful.search.error)
            return

        # iter through results till a suitable image is found
        for res in results:
            image_url: Optional[str]
            if (image_url := getattr(res, "image_url", None)) and not image_url.startswith(
                "x-raw-image://"
            ):
                try:
                    await ctx.reply(res.image_url, mention_author=False)
                except discord.HTTPException as e:
                    if e.code == 50035:
                        await ctx.send(res.image_url)
                    else:
                        raise

                return

        await ctx.reply_embed(ctx.l.useful.search.nope)
        return

    @commands.command(name="remindme", aliases=["remind"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def remind_me(self, ctx: Ctx, duration_str: str, *, reminder: str):
        user_reminder_count = await self.db.fetch_user_reminder_count(ctx.author.id)

        if user_reminder_count > 10:
            await ctx.reply_embed(ctx.l.useful.remind.reminder_max.format(max=10))
            return

        duration = parse_timedelta(duration_str)

        if duration is None:
            await ctx.reply_embed(ctx.l.useful.remind.stupid_1.format(ctx.prefix))
            return

        at = arrow.utcnow() + duration

        if at > arrow.utcnow().shift(weeks=8):
            await ctx.reply_embed(ctx.l.useful.remind.time_max)
            return

        await self.db.add_reminder(
            ctx.author.id,
            ctx.channel.id,
            ctx.message.id,
            reminder[:499].replace("@everyone", "@\uFEFFeveryone").replace("@here", "@\uFEFFhere"),
            at.datetime,
        )
        await ctx.reply_embed(
            ctx.l.useful.remind.remind.format(self.bot.d.emojis.yes, at.humanize(locale=ctx.l.lang, granularity=get_timedelta_granularity(duration, 3)))
        )

    @commands.command(name="snipe")
    async def snipe_message(self, ctx: Ctx):
        snipe = self.snipes.pop(ctx.channel.id, None)

        if snipe is None:
            await ctx.reply_embed(ctx.l.useful.snipe.nothing)
        else:
            snipe, _ = snipe

            embed = discord.Embed(color=self.bot.embed_color, description=snipe.content)
            embed.set_author(
                name=str(snipe.author), icon_url=getattr(snipe.author.avatar, "url", None)
            )
            embed.timestamp = snipe.created_at

            await ctx.send(embed=embed)

    @commands.command(name="redditdl", aliases=["redditsave", "saveredditpost"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def save_reddit_media(self, ctx: Ctx, post_url: str):
        if not post_url.startswith("https://www.reddit.com/r/"):
            await ctx.reply_embed(ctx.l.useful.redditdl.invalid_url)
            return

        post_json_url = post_url.strip().strip("/").split("?")[0] + "/.json"

        async with SuppressCtxManager(ctx.typing()):
            try:
                res = await self.aiohttp.get(post_json_url)
            except aiohttp.client_exceptions.InvalidURL:
                await ctx.reply_embed(ctx.l.useful.redditdl.invalid_url)
                return

            try:
                data = await res.json()
            except json.JSONDecodeError:
                await ctx.reply_embed(ctx.l.useful.redditdl.reddit_error)
                return

            post = data[0]["data"]["children"][0]["data"]

            # check and handle a crosspost
            if post.get("crosspost_parent_list"):
                post = post["crosspost_parent_list"][0]

            post_media = post.get("secure_media") or post.get("media")

            # try to get video
            if post_media and (reddit_video := post_media.get("reddit_video")):
                if reddit_video.get("is_gif"):
                    # is still a video, but no sound, so no need to download and stitch together
                    await ctx.reply(reddit_video["fallback_url"])
                    return

                video_url = reddit_video["fallback_url"]
                audio_url = video_url.replace(f"DASH_{reddit_video['height']}", "DASH_audio")

                video_fname = f"tmp/video_{secrets.token_hex(4)}_{post['name']}.mp4"
                audio_fname = f"tmp/audio_{secrets.token_hex(4)}_{post['name']}.mp4"
                final_fname = f"tmp/final_{secrets.token_hex(4)}_{post['name']}.mp4"

                # download audio and video to temp directory and stitch them together
                try:
                    progress_msg = await ctx.reply(
                        ctx.l.useful.redditdl.downloading.format(self.d.emojis.aniloading),
                        mention_author=False,
                    )
                    asyncio.create_task(ctx.trigger_typing())

                    # stream download video to file
                    async with self.aiohttp.get(video_url) as res, aiofiles.open(
                        video_fname, mode="wb"
                    ) as f:
                        async for data_chunk in res.content.iter_any():
                            await f.write(data_chunk)

                    # stream download audio to file
                    async with self.aiohttp.get(audio_url) as res, aiofiles.open(
                        audio_fname, mode="wb"
                    ) as f:
                        async for data_chunk in res.content.iter_any():
                            await f.write(data_chunk)

                    asyncio.create_task(
                        progress_msg.edit(
                            ctx.l.useful.redditdl.stitching.format(self.d.emojis.aniloading)
                        )
                    )

                    # resize video, stitch video and audio together, then save to file
                    def _ffmpeg_operations():
                        video: moviepy.editor.VideoFileClip = (
                            moviepy.editor.VideoFileClip(video_fname)
                            .resize(0.5)
                            .set_audio(moviepy.editor.AudioFileClip(audio_fname))
                        )
                        video.write_videofile(
                            final_fname, logger=None, threads=4, fps=min(video.fps or 25, 25)
                        )

                    await asyncio.get_event_loop().run_in_executor(self.bot.tp, _ffmpeg_operations)

                    await progress_msg.delete()

                    discord_file = discord.File(
                        final_fname,
                        filename=f"vb_reddit_save_{post['name']}.mp4",
                        description=post["title"],
                    )
                    await ctx.reply(file=discord_file)
                    return
                finally:
                    await asyncio.get_event_loop().run_in_executor(
                        self.bot.tp, os.remove, video_fname
                    )
                    await asyncio.get_event_loop().run_in_executor(
                        self.bot.tp, os.remove, audio_fname
                    )
                    await asyncio.get_event_loop().run_in_executor(
                        self.bot.tp, os.remove, final_fname
                    )

            # try to get image/gif/whatever from preview info
            if preview_media := post.get("preview", {}).get("images"):
                if preview_gif := preview_media[0].get("variants", {}).get("gif"):
                    await ctx.reply(preview_gif["source"]["url"])
                    return

            await ctx.reply(ctx.l.useful.redditdl.couldnt_find)


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Useful(bot))
