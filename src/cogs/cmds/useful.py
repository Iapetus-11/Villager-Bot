from urllib.parse import quote as urlquote
from discord.ext import commands
import async_cse
import asyncio
import discord
import psutil
import arrow


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.v = bot.v

        self.google_client = async_cse.Search(bot.k.google)

        self.db = bot.get_cog("Database")

    @commands.group(name="help")
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            cmd = ctx.message.content.replace(f"{ctx.prefix}help ", "")

            if cmd != "":
                cmd_true = self.bot.get_command(cmd.lower())

                if cmd_true is not None:
                    all_help = {**ctx.l.help.econ, **ctx.l.help.mc, **ctx.l.help.util, **ctx.l.help.fun, **ctx.l.help.mod}

                    help_text = all_help.get(str(cmd_true))

                    if help_text is None:
                        await self.bot.send(ctx, ctx.l.help.main.nodoc)
                        return

                    embed = discord.Embed(color=self.d.cc)

                    embed.set_author(name=ctx.l.help.n.cmd, icon_url=self.d.splash_logo)
                    embed.set_footer(text=ctx.l.misc.petus)

                    embed.description = help_text.format(ctx.prefix)

                    if len(cmd_true.aliases) > 0:
                        embed.description += "\n\n" + ctx.l.help.main.aliases.format("`, `".join(cmd_true.aliases))

                    await ctx.send(embed=embed)

                    return

            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=ctx.l.help.n.title, icon_url=self.d.splash_logo)
            embed.description = ctx.l.help.main.desc.format(self.d.support, self.d.topgg)

            p = ctx.prefix

            embed.add_field(name=(self.d.emojis.emerald_spinn + ctx.l.help.n.economy), value=f"`{p}help econ`")
            embed.add_field(name=(self.d.emojis.bounce + " " + ctx.l.help.n.minecraft), value=f"`{p}help mc`")
            embed.add_field(name=(self.d.emojis.anichest + ctx.l.help.n.utility), value=f"`{p}help util`")

            embed.add_field(name=(self.d.emojis.rainbow_shep + ctx.l.help.n.fun), value=f"`{p}help fun`")
            embed.add_field(name=(self.d.emojis.netherite_sword + ctx.l.help.n.admin), value=f"`{p}help admin`")
            embed.add_field(
                name=(self.d.emojis.heart_spin + ctx.l.help.main.support),
                value=f"**[{ctx.l.help.main.clickme}]({self.d.support})**",
            )

            embed.set_footer(text=ctx.l.useful.credits.foot + "  |  " + ctx.l.useful.rules.slashrules.format(ctx.prefix))

            await ctx.send(embed=embed)

    @help.command(name="economy", aliases=["econ"])
    async def help_economy(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.economy}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        commands_formatted = "`, `".join(list(ctx.l.help.econ))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.send(embed=embed)

    @help.command(name="minecraft", aliases=["mc"])
    async def help_minecraft(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.minecraft}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        commands_formatted = "`, `".join(list(ctx.l.help.mc))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.send(embed=embed)

    @help.command(name="utility", aliases=["util", "useful"])
    async def help_utility(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.utility}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        commands_formatted = "`, `".join(list(ctx.l.help.util))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.send(embed=embed)

    @help.command(name="fun")
    async def help_fun(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.fun}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        commands_formatted = "`, `".join(list(ctx.l.help.fun))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.send(embed=embed)

    @help.command(name="administrator", aliases=["mod", "moderation", "administrative", "admin"])
    async def help_administrative(self, ctx):
        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=f"{ctx.l.help.n.title} [{ctx.l.help.n.admin}]", icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        commands_formatted = "`, `".join(list(ctx.l.help.mod))
        embed.description = f"`{commands_formatted}`\n\n{ctx.l.help.main.howto.format(ctx.prefix)}"

        await ctx.send(embed=embed)

    @commands.command(name="credits", aliases=["creators", "developers"])
    async def credits(self, ctx):
        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name=ctx.l.useful.credits.credits, icon_url=self.d.splash_logo)

        for i, entry in enumerate(ctx.l.useful.credits.people.items()):
            person, what = entry
            user = self.bot.get_user(self.d.credit_users[person])

            embed.add_field(name=f"**{user.display_name}**", value=what)

            if i % 2 == 1:
                embed.add_field(name="\uFEFF", value="\uFEFF")

        embed.add_field(name="\uFEFF", value=ctx.l.useful.credits.others, inline=False)

        await ctx.send(embed=embed)

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
            await self.bot.send(ctx, f"{self.d.emojis.aniheart} Magnum Dong! \uFEFF `69.00 ms`")
            return

        await self.bot.send(ctx, f"{self.d.emojis.aniheart} {pp}! \uFEFF `{round(self.bot.latency*1000, 2)} ms`")

    @commands.command(name="vote", aliases=["votelink", "votelinks"])
    async def votelinks(self, ctx):
        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name="Vote for Villager Bot!", icon_url=self.d.splash_logo)

        embed.description = f'**[{ctx.l.useful.vote.click_1}]({self.d.topgg + "/vote"})**'

        await ctx.send(embed=embed)

    @commands.command(name="links", aliases=["invite", "support", "usefullinks", "website", "source"])
    async def useful_links(self, ctx):
        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name="Useful Links", icon_url=self.d.splash_logo)

        embed.description = (
            f"**[{ctx.l.useful.links.support}]({self.d.support})\n"
            f"\n[{ctx.l.useful.links.invite}]({self.d.invite})\n"
            f"\n[{ctx.l.useful.links.topgg}]({self.d.topgg})\n"
            f"\n[{ctx.l.useful.links.source}]({self.d.github})**"
        )

        await ctx.send(embed=embed)

    @commands.command(name="stats", aliases=["bs"])
    async def stats(self, ctx):
        await ctx.trigger_typing()

        uptime_seconds = (arrow.utcnow() - self.v.start_time).total_seconds()
        uptime = arrow.utcnow().shift(seconds=uptime_seconds).humanize(locale=ctx.l.lang, only_distance=True)

        proc = psutil.Process()
        with proc.oneshot():
            mem_usage = proc.memory_full_info().uss
            threads = proc.num_threads()
            proc.cpu_percent(interval=0.1)

        embed = discord.Embed(color=self.d.cc)

        embed.set_author(name=ctx.l.useful.stats.stats, icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        col_1 = (
            f"{ctx.l.useful.stats.servers}: `{len(self.bot.guilds)}`\n"
            f"{ctx.l.useful.stats.dms}: `{len(self.bot.private_channels)}/128`\n"
            f"{ctx.l.useful.stats.users}: `{len(self.bot.users)}`\n"
            f"{ctx.l.useful.stats.msgs}: `{self.v.msg_count}`\n"
            f"{ctx.l.useful.stats.cmds}: `{self.v.cmd_count}` `({round((self.v.cmd_count / (self.v.msg_count + .000001)) * 100, 2)}%)`\n"
            f"{ctx.l.useful.stats.cmds_sec}: `{round(self.v.cmd_count / uptime_seconds, 2)}`\n"
            f"{ctx.l.useful.stats.votes}: `{self.v.votes_topgg}`\n"
            f"{ctx.l.useful.stats.topgg}: `{round((self.v.votes_topgg / uptime_seconds) * 3600, 2)}`\n"
        )

        col_2 = (
            f"{ctx.l.useful.stats.mem}: `{round(mem_usage / 1000000, 2)} MB`\n"
            f"{ctx.l.useful.stats.cpu}: `{round(proc.cpu_percent() / psutil.cpu_count(), 2)}%`\n"
            f"{ctx.l.useful.stats.threads}: `{threads}`\n"
            f"{ctx.l.useful.stats.tasks}: `{len(asyncio.all_tasks())}`\n"
            f"{ctx.l.useful.stats.ping}: `{round(self.bot.latency * 1000, 2)} ms`\n"
            f"{ctx.l.useful.stats.shards}: `{self.bot.shard_count}`\n"
            f"{ctx.l.useful.stats.uptime}: `{uptime}`\n"
        )

        col_2 += "\n" + ctx.l.useful.stats.more.format(self.d.statcord)

        embed.add_field(name="\uFEFF", value=col_1 + "\uFEFF")
        embed.add_field(name="\uFEFF", value=col_2 + "\uFEFF")

        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["server", "guild"])
    @commands.guild_only()
    async def server_info(self, ctx, gid: int = None):
        if gid is None:
            guild = ctx.guild
        else:
            guild = self.bot.get_guild(gid)

        db_guild = await self.db.fetch_guild(guild.id)

        time = arrow.get(discord.utils.snowflake_time(guild.id))
        time = time.format("MMM D, YYYY", locale=ctx.l.lang) + ", " + time.humanize(locale=ctx.l.lang)

        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name=f"{guild.name} {ctx.l.useful.ginf.info}", icon_url=guild.icon_url)

        embed.description = f"{ctx.l.useful.ginf.age}: `{time}`"

        general = (
            f"{ctx.l.useful.ginf.owner}: {guild.owner.mention}\n"
            f"{ctx.l.useful.ginf.members}: `{guild.member_count}`\n"
            f"{ctx.l.useful.ginf.channels}: `{len(guild.channels)}`\n "
            f"{ctx.l.useful.ginf.roles}: `{len(guild.roles)}`\n"
            f"{ctx.l.useful.ginf.emojis}: `{len(guild.emojis)}`\n"
            f"{ctx.l.useful.ginf.bans}: `{len(await guild.bans())}`\n"
        )

        villager = (
            f"{ctx.l.useful.ginf.cmd_prefix}: `{self.v.prefix_cache.get(guild.id, self.d.default_prefix)}`\n"
            f"{ctx.l.useful.ginf.lang}: `{ctx.l.name}`\n"
            f'{ctx.l.useful.ginf.diff}: `{db_guild["difficulty"]}`\n'
            f'{ctx.l.useful.ginf.prem}: `{str(db_guild["premium"]).lower()}`\n'
        )

        embed.add_field(name="General", value=general, inline=True)
        embed.add_field(name="Villager Bot", value=villager, inline=True)

        embed.set_thumbnail(url=guild.icon_url)

        await ctx.send(embed=embed)

    @commands.command(name="rules", aliases=["botrules"])
    async def rules(self, ctx):
        embed = discord.Embed(color=self.d.cc, description=ctx.l.useful.rules.penalty)

        embed.set_author(name=ctx.l.useful.rules.rules, icon_url=self.d.splash_logo)
        embed.set_footer(text=ctx.l.misc.petus)

        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_1.format(self.d.support))
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_2)

        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_3)
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name="\uFEFF", value=ctx.l.useful.rules.rule_4)

        await ctx.send(embed=embed)

    @commands.command(name="math", aliases=["solve", "meth"])
    async def math(self, ctx, *, problem):
        async with ctx.typing():
            try:
                resp = await self.bot.aiohttp.get(f"https://api.mathjs.org/v4/?expr={urlquote(problem)}")
                await self.bot.send(ctx, f"```{float(await resp.text())}```")
            except Exception:
                await self.bot.send(ctx, ctx.l.useful.meth.oops)

    @commands.command(name="google", aliases=["thegoogle"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def google_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with ctx.typing():
                res = await self.google_client.search(query, safesearch=safesearch)
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        embed = discord.Embed(color=self.d.cc, title=res.title, description=res.description, url=res.url)
        await ctx.send(embed=embed)

    @commands.command(name="youtube", aliases=["ytsearch", "yt"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def youtube_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with ctx.typing():
                res = await self.google_client.search(query, safesearch=safesearch)
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        res = tuple(filter((lambda r: "youtube.com/watch" in r.url), res))

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        await ctx.send(res.url)

    @commands.command(name="image", aliases=["imagesearch", "img"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def image_search(self, ctx, *, query):
        safesearch = True
        if isinstance(ctx.channel, discord.TextChannel):
            safesearch = not ctx.channel.is_nsfw()

        try:
            async with ctx.typing():
                res = await self.google_client.search(query, safesearch=safesearch, image_search=True)
        except async_cse.search.NoResults:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return
        except async_cse.search.APIError:
            await self.bot.send(ctx, ctx.l.useful.search.error)
            return

        if len(res) == 0:
            await self.bot.send(ctx, ctx.l.useful.search.nope)
            return

        res = res[0]

        await ctx.send(res.image_url)

    @commands.command(name="remindme", aliases=["remind"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def remind_me(self, ctx, *, args: str):
        user_reminder_count = await self.db.fetch_user_reminder_count(ctx.author.id)

        if user_reminder_count > 5:
            await self.bot.send(ctx, ctx.l.useful.remind.reminder_max)
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
            await self.bot.send(ctx, ctx.l.useful.remind.stupid_1.format(ctx.prefix))
            return

        if at > arrow.utcnow().shift(weeks=8):
            await self.bot.send(ctx, ctx.l.useful.remind.time_max)
            return

        await self.db.add_reminder(ctx.author.id, ctx.channel.id, ctx.message.id, " ".join(args[i:])[:499], at.timestamp())
        await self.bot.send(ctx, ctx.l.useful.remind.remind.format(self.bot.d.emojis.yes, at.humanize(locale=ctx.l.lang)))


def setup(bot):
    bot.add_cog(Useful(bot))
