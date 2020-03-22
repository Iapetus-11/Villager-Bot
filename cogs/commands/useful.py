from discord.ext import commands
import discord
import arrow
from googlesearch import search


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")

    @commands.command(name="help") # Displays help messages
    async def helpp(self, ctx):
        msg = ctx.message.clean_content.lower().replace(ctx.prefix+"help ", "").replace(ctx.prefix+"help", "")
        helpMsg = discord.Embed(description="", color=discord.Color.green())
        helpMsg.set_author(name="Villager Bot Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        helpMsg.set_footer(text="Made by Iapetus11#6821")

        if msg == "mc":
            helpMsg.add_field(name="__**Minecraft Stuff**__", value="""
**{0}mcping** ***ip:port*** *to check the status of a Java Edition Minecraft server*
**{0}mcpeping** ***ip*** *to check the status of a Bedrock Edition Minecraft server*
**{0}stealskin** ***gamertag*** *steal another player's Minecraft skin*
**{0}nametouuid** ***gamertag*** *gets the Minecraft uuid of the given player*
**{0}uuidtoname** ***uuid*** *gets the gamertag from the given Minecraft uuid*
**{0}randommc** *sends a random Minecraft server*
""".format(ctx.prefix), inline=True)
            await ctx.send(embed=helpMsg)
            return

        elif msg == "fun":
            helpMsg.add_field(name="__**Text Commands**__", value="""
**{0}villagerspeak** ***text*** *turns English text into villager sounds*
**{0}enchant** ***text*** *turns english text into the Minecraft enchantment table language, a.k.a. the Standard Galactic Alphabet.*
**{0}unenchant** ***text*** *turns the enchanting table language back into English*
**{0}sarcastic** ***text*** *makes text sarcastic*
**{0}say** ***text*** *bot will repeat what you tell it to*
""".format(ctx.prefix), inline=False)
            helpMsg.add_field(name="__**Currency Commands**__", value="""
**{0}mine** *go mining with the bot for emeralds*
**{0}balance** *the bot will tell you how many emeralds you have*
**{0}inventory** *see what you have in your inventory*
**{0}give** ***@user*** ***amount*** *give mentioned user emeralds*
**{0}gamble** ***amount*** *gamble with Villager Bot*
**{0}pillage** ***@user*** *attempt to steal emeralds from another person*
**{0}shop** *go shopping with emeralds*
**{0}deposit** ***amount in emerald blocks*** *deposit emerald blocks into the emerald vault*
**{0}withdraw** ***amount in emerald blocks*** *withdraw emerald blocks from the emerald vault*
**{0}leaderboard** *shows the emerald leaderboard*
""".format(ctx.prefix), inline=False)
            helpMsg.add_field(name="__**Other Commands**__", value="""
**{0}cursed** *the bot will upload a cursed Minecraft image*
**{0}battle** ***user*** *allows you to battle your friends!*
""".format(ctx.prefix), inline=False)
            await ctx.send(embed=helpMsg)
            return

        elif msg == "useful":
            helpMsg.add_field(name="__**Useful/Informative**__", value="""
**{0}help** *displays this help message*
**{0}info** *displays information about the bot*
**{0}ping** *to see the bot's latency between itself and the Discord API*
**{0}uptime** *to check how long the bot has been online*
**{0}votelink** *to get the link to vote for and support the bot!*
**{0}invite** *to get the link to add Villager Bot to your own server!*
**{0}google** ***query*** *bot will search on google for your query*
**{0}youtube** ***query*** *bot will search on youtube for your query*
**{0}reddit** ***query*** *bot will search on reddit for your query*
""".format(ctx.prefix), inline=True)
            await ctx.send(embed=helpMsg)
            return

        elif msg == "admin":
            helpMsg.add_field(name="__**Admin Only**__", value="""
**{0}config** *change the settings of the bot for your server*
**{0}purge** ***number of messages*** *deletes n number of messages in the channel it's summoned in*
**{0}kick** ***@user*** *kicks the mentioned user*
**{0}ban** ***@user*** *bans the mentioned user*
**{0}pardon** ***@user*** *unbans the mentioned user*
""".format(ctx.prefix), inline=True)
            await ctx.send(embed=helpMsg)
            return

        else:
            helpMsg.add_field(name="Minecraft", value="``"+ctx.prefix+"help mc``", inline=True)
            helpMsg.add_field(name="Fun", value="``"+ctx.prefix+"help fun``", inline=True)
            helpMsg.add_field(name="Useful", value="``"+ctx.prefix+"help useful``", inline=True)
            helpMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            helpMsg.add_field(name="Admin", value="``"+ctx.prefix+"help admin``", inline=True)
            helpMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            helpMsg.add_field(name="\uFEFF", value="""Need more help? Check out the Villager Bot [Support Server](https://discord.gg/39DwwUV)
Enjoying the bot? Vote for us on [top.gg](https://top.gg/bot/639498607632056321/vote)""", inline=False)
            await ctx.send(embed=helpMsg)

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

    @commands.command(name="ping", aliases=["pong"]) # Checks latency between Discord API and the bot
    async def ping(self, ctx):
        if ctx.message.content.lower().replace(ctx.prefix, "") == "pong":
            pp = "Ping"
        else:
            pp = "Pong"
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{pp}! {round(self.bot.latency*1000, 2)} ms"))

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
