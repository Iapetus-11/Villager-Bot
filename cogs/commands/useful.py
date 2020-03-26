from discord.ext import commands
import discord
import arrow
from googlesearch import search


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")

    @commands.group(name="help")
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            help_embed = discord.Embed(color=discord.Color.green())
            help_embed.set_author(
                name="Villager Bot Commands",
                icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

            help_embed.add_field(name="Minecraft", value=f"``{ctx.prefix}help mc``", inline=False)
            help_embed.add_field(name="Fun", value=f"``{ctx.prefix}help fun``", inline=False)
            help_embed.add_field(name="Useful", value=f"``{ctx.prefix}help useful``", inline=False)
            help_embed.add_field(name="Admin", value=f"``{ctx.prefix}help admin``", inline=False)
            help_embed.add_field(name="\uFEFF", value="""Need more help? Check out the Villager Bot [Support Server](https://discord.gg/39DwwUV)
            Enjoying the bot? Vote for us on [top.gg](https://top.gg/bot/639498607632056321/vote)""", inline=False)

            help_embed.set_footer(text="Made by Iapetus11#6821 & TrustedMercury#1953")

            await ctx.send(embed=help_embed)

    @help.command(name='fun')
    async def fun(self, ctx):

        help_embed = discord.Embed(color=discord.Color.green())
        help_embed.set_author(
            name="Villager Bot Commands",
            icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

        help_embed.add_field(
            name="**Text Commands**",
            value=f'**{ctx.prefix}villagerspeak** ***text*** *turns English text into villager sounds*\n'
            f'**{ctx.prefix}enchant** ***text*** *turns english text into the Minecraft enchantment table language, a.k.a. the Standard Galactic Alphabet.*\n'
            f'**{ctx.prefix}unenchant** ***text*** *turns the enchanting table language back into English*\n'
            f'**{ctx.prefix}sarcastic** ***text*** *makes text sarcastic*\n'
            f'**{ctx.prefix}say** ***text*** *bot will repeat what you tell it to*\n',
            inline=False)

    @help.command(name='useful')
    async def useful(self, ctx):

        help_embed = discord.Embed(color=discord.Color.green())
        help_embed.set_author(
            name="Villager Bot Commands",
            icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

        help_embed.add_field(
            name="**Useful/Informative**",
            value=f'**{ctx.prefix}help** *displays this help message*\n'
            f'**{ctx.prefix}info** *displays information about the bot*\n'
            f"**{ctx.prefix}ping** *to see the bot's latency between itself and the Discord API*'\n"
            f'**{ctx.prefix}uptime** *to check how long the bot has been online*\n'
            f'**{ctx.prefix}votelink** *to get the link to vote for and support the bot!*\n'
            f'**{ctx.prefix}invite** *to get the link to add Villager Bot to your own server!*\n'
            f'**{ctx.prefix}google** ***query*** *bot will search on google for your query*\n'
            f'**{ctx.prefix}youtube** ***query*** *bot will search on youtube for your query*\n'
            f'**{ctx.prefix}reddit** ***query*** *bot will search on reddit for your query*\n',
            inline=True)
        await ctx.send(embed=help_embed)

    @help.command(name='admin')
    async def admin(self, ctx):

        help_embed = discord.Embed(color=discord.Color.green())
        help_embed.set_author(
            name="Villager Bot Commands",
            icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

        help_embed.add_field(
            name="**Admin Only**",
            value=f'**{ctx.prefix}config** *change the settings of the bot for your server*\n'
            f"**{ctx.prefix}purge** ***number of messages*** *deletes n number of messages in the channel it's summoned in*\n"
            f'**{ctx.prefix}kick** ***@user*** *kicks the mentioned user*\n'
            f'**{ctx.prefix}ban** ***@user*** *bans the mentioned user*\n'
            f'**{ctx.prefix}pardon** ***@user*** *unbans the mentioned user*\n',
            inline=True)
        await ctx.send(embed=help_embed)

    @commands.command(name="info", aliases=["information"])
    async def information(self, ctx):
        infoMsg = discord.Embed(color=discord.Color.green())
        infoMsg.add_field(name="Creator", value="Iapetus11#6821", inline=True)
        infoMsg.add_field(name="Bot Library", value="Discord.py", inline=True)
        infoMsg.add_field(name="Command Prefix", value=ctx.prefix, inline=True)
        infoMsg.add_field(name="Total Servers", value=str(len(self.bot.guilds)), inline=True)
        infoMsg.add_field(name="Shards", value=str(self.bot.shard_count), inline=True)
        infoMsg.add_field(name="Total Users", value=str(len(self.bot.users)), inline=True)
        infoMsg.add_field(name="Bot Page", value="[Click Here](https://top.gg/bot/639498607632056321)", inline=True)
        infoMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        infoMsg.add_field(name="Discord", value="[Click Here](https://discord.gg/39DwwUV)", inline=True)
        infoMsg.set_author(name="Villager Bot Information", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=infoMsg)

    @commands.command(name="ping", aliases=["pong", "ding", "dong"]) # Checks latency between Discord API and the bot
    async def ping(self, ctx):
        c = ctx.message.content.lower()
        if "pong" in c:
            pp = "Ping"
        elif "ping" in c:
            pp = "Pong"
        elif "ding" in c:
            pp = "Dong"
        elif "dong" in c:
            pp = "Ding"
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"<a:ping:692401875001278494> {pp}! \uFEFF ``{round(self.bot.latency*1000, 2)} ms``"))

    @commands.command(name="uptime")
    async def getuptime(self, ctx):
        p = arrow.utcnow()
        diff = (p - self.g.startTime)
        days = diff.days
        hours = int(diff.seconds / 3600)
        minutes = int(diff.seconds / 60) % 60
        if days == 1:
            dd = "day"
        else:
            dd = "days"
        if hours == 1:
            hh = "hour"
        else:
            hh = "hours"
        if minutes == 1:
            mm = "minute"
        else:
            mm = "minutes"
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bot has been online for "+str(days)+" "+dd+", "+str(hours)+" "+hh+", and "+str(minutes)+" "+mm+"!"))

    @commands.command(name="vote", aliases=["votelink"])
    async def votelink(self, ctx):
        voteL = discord.Embed(title="Vote for Villager Bot", description="[Click Here!](https://top.gg/bot/639498607632056321/vote)", color=discord.Color.green())
        voteL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=voteL)

    @commands.command(name="invite", aliases=["invitelink"])
    async def inviteLink(self, ctx):
        invL = discord.Embed(title="Add Villager Bot to your server", description="[Click Here!](https://bit.ly/2tQfOhW)", color=discord.Color.green())
        invL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=invL)

    @commands.command(name="google")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def googleSearch(self, ctx, *, query: str):
        await ctx.trigger_typing()
        rs = []
        for result in search(query, tld="co.in", num=1, stop=1, pause=0):
            rs.append(result)
        if len(rs) > 0:
            await ctx.send(rs[0])
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for query \""+query+"\""))

    @commands.command(name="youtube")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def ytSearch(self, ctx, *, query: str):
        await ctx.trigger_typing()
        rs = []
        for result in search(query, tld="co.in", domains=["youtube.com"], num=1, stop=1, pause=0):
            rs.append(result)
        if len(rs) > 0:
            await ctx.send(rs[0])
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for query \""+query+"\""))

    @commands.command(name="reddit")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def redditSearch(self, ctx, *, query: str):
        await ctx.trigger_typing()
        rs = []
        for result in search(query, tld="co.in", domains=["reddit.com"], num=1, stop=1, pause=0):
            rs.append(result)
        if len(rs) > 0:
            await ctx.send(rs[0])
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for query \""+query+"\""))


def setup(bot):
    bot.add_cog(Useful(bot))
