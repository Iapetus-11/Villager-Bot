from urllib.parse import quote as urlquote
from disnake.ext import commands, tasks
from contextlib import suppress
import async_cse
import asyncio
import disnake
import psutil
import arrow
import time

from util.misc import SuppressCtxManager
from util.ipc import PacketType


class BanCacheEntry:
    __slots__ = ("ban_count", "time")

    def __init__(self, ban_count: int):
        self.ban_count = ban_count
        self.time = time.time()


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.db = bot.get_cog("Database")
        self.ipc = bot.ipc
        self.google = async_cse.Search(bot.k.google_search)
        self.aiohttp = bot.aiohttp

        self.ban_count_cache = {}

        self.snipes = {}
        self.clear_snipes.start()

    def cog_unload(self):
        self.clear_snipes.cancel()

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
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            cmd = ctx.message.content.replace(f"{ctx.prefix}help ", "")

            if cmd != "":
                cmd_true = self.bot.get_command(cmd.lower())

                if cmd_true is not None:
                    all_help = {**ctx.l.help.econ, **ctx.l.help.mc, **ctx.l.help.util, **ctx.l.help.fun, **ctx.l.help.mod}

                    help_text = all_help.get(str(cmd_true))

                    if help_text is None:
                        await ctx.reply_embed(ctx.l.help.main.nodoc)
                        return

                    embed = disnake.Embed(color=self.d.cc)

                    embed.set_author(name=ctx.l.help.n.cmd, icon_url=self.d.splash_logo)
                    embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

                    embed.description = help_text.format(ctx.prefix)

                    if len(cmd_true.aliases) > 0:
                        embed.description += "\n\n" + ctx.l.help.main.aliases.format("`, `".join(cmd_true.aliases))

                    try:
                        await ctx.reply(embed=embed, mention_author=False)
                    except disnake.errors.HTTPException as e:
                        if (
                            e.code == 50035
                        ):  # invalid form body, happens sometimes when the message to reply to can't be found?
                            await ctx.send(embed=embed, mention_author=False)
                        else:
                            raise

                    return

            embed = disnake.Embed(color=self.d.cc)
            embed.set_author(name=ctx.l.help.n.title, icon_url=self.d.splash_logo)
            embed.description = ctx.l.help.main.desc.format(self.d.support, self.d.topgg)

            p = ctx.prefix

            embed.add_field(name=(self.d.emojis.emerald_spinn + ctx.l.help.n.economy), value=f"`{p}help econ`")
            embed.add_field(name=(self.d.emojis.bounce + " " + ctx.l.help.n.minecraft), value=f"`{p}help mc`")
            embed.add_field(name=(self.d.emojis.anichest + ctx.l.help.n.utility), value=f"`{p}help util`")

            embed.add_field(name=(self.d.emojis.rainbow_shep + ctx.l.help.n.fun), value=f"`{p}help fun`")
            embed.add_field(name=(self.d.emojis.netherite_sword_ench + ctx.l.help.n.admin), value=f"`{p}help admin`")
            embed.add_field(
                name=(self.d.emojis.heart_spin + ctx.l.help.main.support),
                value=f"**[{ctx.l.help.main.clickme}]({self.d.support})**",
            )

            embed.set_footer(
                text=ctx.l.useful.credits.foot.format(ctx.prefix) + "  |  " + ctx.l.useful.rules.slashrules.format(ctx.prefix)
            )

            await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="economy", aliases=["econ"])
    async def help_economy(self, ctx):
        embed = disnake.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.economy}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.econ))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="minecraft", aliases=["mc"])
    async def help_minecraft(self, ctx):
        embed = disnake.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.minecraft}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.mc))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="utility", aliases=["util", "useful"])
    async def help_utility(self, ctx):
        embed = disnake.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.utility}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.util))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="fun")
    async def help_fun(self, ctx):
        embed = disnake.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.fun}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.fun))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @help.command(name="administrator", aliases=["mod", "moderation", "administrative", "admin"])
    async def help_administrative(self, ctx):
        embed = disnake.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.admin}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        commands_formatted = "`, `".join(list(ctx.l.help.mod))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="credits")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def credits(self, ctx):
        embed_template = disnake.Embed(color=self.d.cc)
        embed_template.set_author(name=ctx.l.useful.credits.credits, icon_url=self.d.splash_logo)

        fields = []

        for i, entry in enumerate(ctx.l.useful.credits.people.items()):
            person, what = entry
            user = self.bot.get_user(self.d.credit_users[person])

            if user is None:
                user = await self.bot.fetch_user(self.d.credit_users[person])

            fields.append({"name": f"**{user.display_name}**", "value": what})

            if i % 2 == 1:
                fields.append({"value": "\uFEFF", "name": "\uFEFF"})

        groups = [fields[i : i + 9] for i in range(0, len(fields), 9)]
        page_max = len(groups)
        page = 0
        msg = None

        while True:
            embed = embed_template.copy()

            for field in groups[page]:
                embed.add_field(**field)

            embed.set_footer(text=f"{ctx.l.econ.page} {page+1}/{page_max}")

            if page == page_max - 1:
                embed.add_field(name="\uFEFF", value=ctx.l.useful.credits.others, inline=False)

            if msg is None:
                msg = await ctx.reply(embed=embed, mention_author=False)
            elif not msg.embeds[0] == embed:
                await msg.edit(embed=embed)

            if page_max <= 1:
                return

            await asyncio.sleep(0.25)
            await msg.add_reaction("⬅️")
            await asyncio.sleep(0.25)
            await msg.add_reaction("➡️")

            try:

                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg == react.message

                # wait for reaction from message author (1 min)
                react, r_user = await self.bot.wait_for("reaction_add", check=author_check, timeout=30)
            except asyncio.TimeoutError:
                await asyncio.wait((msg.remove_reaction("⬅️", ctx.me), msg.remove_reaction("➡️", ctx.me)))
                return

            await react.remove(ctx.author)

            if react.emoji == "⬅️":
                page -= 1
            elif react.emoji == "➡️":
                page += 1

            if page > page_max - 1:
                page = page_max - 1

            if page < 0:
                page = 0

            await asyncio.sleep(0.2)

    @commands.command(name="avatar", aliases=["av"])
    async def member_avatar(self, ctx, member: disnake.Member = None):
        member = member or ctx.author
        embed = disnake.Embed(color=self.d.cc, description=f"[Download]({member.avatar.url})")
        embed.set_image(url=member.avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="ping", aliases=["pong", "ding", "dong", "bing", "bong", "shing", "shling", "schlong"])
    async def ping_pong(self, ctx):
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

        await ctx.reply_embed(f"{self.d.emojis.aniheart} {pp}! \uFEFF `{round(self.bot.latency*1000, 2)} ms`")

    @commands.command(name="vote", aliases=["votelink", "votelinks"])
    async def votelinks(self, ctx):
        embed = disnake.Embed(color=self.d.cc)
        embed.set_author(name="Vote for Villager Bot!", icon_url=self.d.splash_logo)

        embed.description = f'**[{ctx.l.useful.vote.click_1}]({self.d.topgg + "/vote"})**'

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="links", aliases=["invite", "support", "usefullinks", "website", "source", "privacypolicy"])
    async def useful_links(self, ctx):
        embed = disnake.Embed(color=self.d.cc)
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
    async def stats(self, ctx):
        with suppress(Exception):
            await ctx.trigger_typing()

        uptime_seconds = (arrow.utcnow() - self.bot.start_time).total_seconds()
        uptime = arrow.utcnow().shift(seconds=uptime_seconds).humanize(locale=ctx.l.lang, only_distance=True)

        res, karen_res = await asyncio.gather(
            self.ipc.broadcast({"type": PacketType.FETCH_STATS}), self.ipc.request({"type": PacketType.FETCH_STATS})
        )

        res.responses.append(karen_res)

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
        ) = map(sum, zip(*[r.stats for r in res.responses]))

        total_mem = psutil.virtual_memory().total

        embed = disnake.Embed(color=self.d.cc)

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
            f"{ctx.l.useful.stats.ping}: `{round((latency_all/len(res.responses)) * 1000, 2)} ms`\n"
            f"{ctx.l.useful.stats.shards}: `{self.bot.k.shard_count}`\n"
            f"{ctx.l.useful.stats.uptime}: `{uptime}`\n"
        )

        col_2 += "\n" + ctx.l.useful.stats.more.format(self.d.statcord)

        embed.add_field(name="\uFEFF", value=col_1 + "\uFEFF")
        embed.add_field(name="\uFEFF", value=col_2 + "\uFEFF")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="serverinfo", aliases=["server", "guild", "guildinfo"])
    @commands.guild_only()
    async def server_info(self, ctx, *, guild: disnake.Guild = None):
        with suppress(Exception):
            await ctx.trigger_typing()

        if guild is None:
            guild = ctx.guild

        db_guild = await self.db.fetch_guild(guild.id)

        age = arrow.get(disnake.utils.snowflake_time(guild.id))
        display_age = age.format("MMM D, YYYY", locale=ctx.l.lang) + ", " + age.humanize(locale=ctx.l.lang)

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

        embed = disnake.Embed(color=self.d.cc)
        embed.set_author(name=f"{guild.name} {ctx.l.useful.ginf.info}", icon_url=getattr(guild.icon, "url", embed.Empty))

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
            f'{ctx.l.useful.ginf.diff}: `{db_guild["difficulty"]}`\n'
            f"{ctx.l.useful.ginf.cmd_prefix}: `{await self.bot.get_prefix(ctx)}`\n"
        )

        embed.add_field(name="General :gear:", value=general, inline=True)
        embed.add_field(name="Villager Bot " + self.d.emojis.emerald, value=villager, inline=True)
        # embed.add_field(name="Roles", value=" ".join([r.mention for r in guild.roles if r.id != guild.id][::-1]))

        embed.set_thumbnail(url=getattr(guild.icon, "url", embed.Empty))
        embed.set_footer(text=ctx.l.useful.credits.foot.format(ctx.prefix))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="rules", aliases=["botrules"])
    async def rules(self, ctx):
        embed = disnake.Embed(color=self.d.cc, description=ctx.l.useful.rules.penalty)

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
    async def math(self, ctx, *, problem):
        async with SuppressCtxManager(ctx.typing()):
            try:
                resp = await self.aiohttp.get(f"https://api.mathjs.org/v4/?expr={urlquote(problem)}")
                await ctx.reply_embed(f"```{float(await resp.text())}```")
            except Exception:
                await ctx.reply_embed(ctx.l.useful.meth.oops)

    @commands.command(name="google", aliases=["thegoogle", "gewgle"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def google_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, disnake.TextChannel):
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

        embed = disnake.Embed(color=self.d.cc, title=res.title, description=res.description, url=res.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="youtube", aliases=["ytsearch", "yt"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def youtube_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, disnake.TextChannel):
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
    async def image_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, disnake.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with SuppressCtxManager(ctx.typing()):
                res = await self.google.search(query, safesearch=safesearch, image_search=True)
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

        try:
            await ctx.reply(res.image_url, mention_author=False)
        except disnake.HTTPException as e:
            if e.code == 50035:
                await ctx.send(res.image_url)
            else:
                raise

    @commands.command(name="remindme", aliases=["remind"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def remind_me(self, ctx, *, args: str):
        user_reminder_count = await self.db.fetch_user_reminder_count(ctx.author.id)

        if user_reminder_count > 5:
            await ctx.reply_embed(ctx.l.useful.remind.reminder_max)
            return

        args = ctx.message.clean_content[len(f"{ctx.prefix}{ctx.invoked_with} ") :].split()
        at = arrow.utcnow()
        i = 0

        try:
            for i, arg in enumerate(args):
                if arg.endswith("m"):
                    at = at.shift(minutes=int(arg[:-1]))
                elif arg.endswith("minute"):
                    at = at.shift(minutes=int(arg[:-6]))
                elif arg.endswith("minutes"):
                    at = at.shift(minutes=int(arg[:-7]))
                elif arg.endswith("h"):
                    at = at.shift(hours=int(arg[:-1]))
                elif arg.endswith("hour"):
                    at = at.shift(hours=int(arg[:-4]))
                elif arg.endswith("hours"):
                    at = at.shift(hours=int(arg[:-5]))
                elif arg.endswith("d"):
                    at = at.shift(days=int(arg[:-1]))
                elif arg.endswith("day"):
                    at = at.shift(days=int(arg[:-3]))
                elif arg.endswith("days"):
                    at = at.shift(days=int(arg[:-4]))
                elif arg.endswith("w"):
                    at = at.shift(weeks=int(arg[:-1]))
                elif arg.endswith("week"):
                    at = at.shift(weeks=int(arg[:-4]))
                elif arg.endswith("weeks"):
                    at = at.shift(weeks=int(arg[:-5]))
                else:
                    break
        except ValueError:
            pass

        if i == 0:
            await ctx.reply_embed(ctx.l.useful.remind.stupid_1.format(ctx.prefix))
            return

        if at > arrow.utcnow().shift(weeks=8):
            await ctx.reply_embed(ctx.l.useful.remind.time_max)
            return

        await self.db.add_reminder(ctx.author.id, ctx.channel.id, ctx.message.id, " ".join(args[i:])[:499], at.datetime)
        await ctx.reply_embed(ctx.l.useful.remind.remind.format(self.bot.d.emojis.yes, at.humanize(locale=ctx.l.lang)))

    @commands.command(name="snipe")
    async def snipe_message(self, ctx):
        snipe = self.snipes.pop(ctx.channel.id, None)

        if snipe is None:
            await ctx.reply_embed(ctx.l.useful.snipe.nothing)
        else:
            snipe, _ = snipe

            embed = disnake.Embed(color=self.d.cc, description=snipe.content)
            embed.set_author(name=str(snipe.author), icon_url=getattr(snipe.author.avatar, "url", embed.Empty))
            embed.timestamp = snipe.created_at

            await ctx.send(embed=embed)

    # @commands.command(name="downloadredditvideo", aliases=["dlreddit", "redditdl", "vredditdl", "dlredditvideo"])
    # @commands.cooldown(1, 2, commands.BucketType.user)
    # async def reddit_media_download(self, ctx, post_url: str):
    #     if not post_url.startswith("https://www.reddit.com/r/"):
    #         await ctx.reply_embed(ctx.l.useful.vredditdl.invalid_url)
    #         return

    #     async with SuppressCtxManager(ctx.typing()):
    #         try:
    #             d = await (await self.aiohttp.get(post_url.rstrip(".json") + ".json")).json()
    #             await ctx.send(
    #                 ctx.l.useful.vredditdl.here_ya_go
    #                 + " "
    #                 + d[0]["data"]["children"][0]["data"]["media"]["reddit_video"]["fallback_url"].split("?")[0]
    #             )
    #         except aiohttp.client_exceptions.InvalidURL:
    #             await ctx.reply_embed(ctx.l.useful.vredditdl.invalid_url)
    #             return
    #         except (IndexError, KeyError) as e:
    #             print(e)
    #             await ctx.reply_embed(ctx.l.useful.vredditdl.no_media)


def setup(bot):
    bot.add_cog(Useful(bot))
