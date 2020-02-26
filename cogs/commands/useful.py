from discord.ext import commands
import discord
import arrow
from googlesearch import search

class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")
    
    @commands.command(name="help") #displays help messages
    async def helpp(self, ctx):
        msg = ctx.message.clean_content[7:]
        helpMsg = discord.Embed(
            description = "",
            color = discord.Color.green()
        )
        helpMsg.set_author(name="Villager Bot Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        helpMsg.set_footer(text="Made by Iapetus11#6821")
        
        if msg == "mc":
            helpMsg.add_field(name="__**Minecraft Stuff**__", value="""
**!!mcping** ***ip:port*** *to check the status of a Java Edition Minecraft server*
**!!mcpeping** ***ip*** *to check the status of a Bedrock Edition Minecraft server*
**!!stealskin** ***gamertag*** *steal another player's Minecraft skin*
""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        elif msg == "fun":
            helpMsg.add_field(name="__**Text Commands**__", value="""
**!!villagerspeak** ***text*** *turns English text into villager sounds*
**!!enchant** ***text*** *turns english text into the Minecraft enchantment table language, a.k.a. the Standard Galactic Alphabet.*
**!!unenchant** ***text*** *turns the enchanting table language back into English*
**!!sarcastic** ***text*** *makes text sarcastic*
**!!say** ***text*** *bot will repeat what you tell it to*
""", inline=False)
            helpMsg.add_field(name="__**Currency Commands**__", value="""
**!!mine** *go mining with the bot for emeralds*
**!!balance** *the bot will tell you how many emeralds you have*
**!!inventory** *see what you have in your inventory*
**!!give** ***@user*** ***amount*** *give mentioned user emeralds*
**!!gamble** ***amount*** *gamble with Villager Bot*
**!!pillage** ***@user*** *attempt to steal emeralds from another person*
**!!shop** *go shopping with emeralds*
**!!deposit** ***amount in emerald blocks*** *deposit emerald blocks into the emerald vault*
**!!withdraw** ***amount in emerald blocks*** *withdraw emerald blocks from the emerald vault*
""", inline=False)
            helpMsg.add_field(name="__**Other Commands**__", value="""
**!!cursed** *the bot will upload a cursed Minecraft image*
**!!battle** ***user*** *allows you to battle your friends!*
""", inline=False)
            await ctx.send(embed=helpMsg)
            return
        
        elif msg == "useful":        
            helpMsg.add_field(name="__**Useful/Informative**__", value="""
**!!help** *displays this help message*
**!!info** *displays information about the bot*
**!!ping** *to see the bot's latency between itself and the Discord API*
**!!uptime** *to check how long the bot has been online*
**!!votelink** *to get the link to vote for and support the bot!*
**!!invite** *to get the link to add Villager Bot to your own server!*
**!!google** ***query*** *bot will search on google for your query*
**!!youtube** ***query*** *bot will search on youtube for your query*
**!!reddit** ***query*** *bot will search on reddit for your query*
""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        elif msg == "admin":        
            helpMsg.add_field(name="__**Admin Only**__", value="""
**!!purge** ***number of messages*** *deletes n number of messages in the channel it's summoned in*
**!!kick** ***@user*** *kicks the mentioned user*
**!!ban** ***@user*** *bans the mentioned user*
**!!pardon** ***@user*** *unbans the mentioned user*""", inline=True)
            await ctx.send(embed=helpMsg)
            return
        
        else:
            helpMsg.add_field(name="Minecraft", value="``!!help mc``", inline=True)
            helpMsg.add_field(name="Fun", value="``!!help fun``", inline=True)
            helpMsg.add_field(name="Useful", value="``!!help useful``", inline=True)
            helpMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            helpMsg.add_field(name="Admin", value="``!!help admin``", inline=True)
            helpMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            helpMsg.add_field(name="\uFEFF", value="""Need more help? Check out the Villager Bot [Support Server](https://discord.gg/39DwwUV)
Enjoying the bot? Vote for us on [top.gg](https://top.gg/bot/639498607632056321/vote)""", inline=False)
            await ctx.send(embed=helpMsg)

    @commands.command(name="info", aliases=["information"])
    async def information(self, ctx):        
        infoMsg = discord.Embed(
             color = discord.Color.green()
        )
        infoMsg.add_field(name="Creator", value="Iapetus11#6821", inline=True)
        infoMsg.add_field(name="Bot Library", value="Discord.py", inline=True)
        infoMsg.add_field(name="Command Prefix", value="!!", inline=True)
        infoMsg.add_field(name="Total Servers", value=str(len(self.bot.guilds)), inline=True)
        infoMsg.add_field(name="Shards", value=str(self.bot.shard_count), inline=True)
        infoMsg.add_field(name="Total Users", value=str(len(self.bot.users)), inline=True)
        infoMsg.add_field(name="Bot Page", value="[Click Here](https://top.gg/bot/639498607632056321)", inline=True)
        infoMsg.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        infoMsg.add_field(name="Discord", value="[Click Here](https://discord.gg/39DwwUV)", inline=True)
        infoMsg.set_author(name="Villager Bot Information", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=infoMsg)

    @commands.command(name="ping", aliases=["latency"]) #checks latency between Discord API and the bot
    async def ping(self, ctx):
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Pong! "+str(round(self.bot.latency*1000, 2))+" ms"))

    @commands.command(name="uptime")
    async def getuptime(self, ctx):
        p = arrow.utcnow()
        diff = (p - self.g.startTime)
        days = diff.days
        hours = int(diff.seconds/3600)
        minutes = int(diff.seconds/60)%60
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
        voteL = discord.Embed(
             title = "Vote for Villager Bot",
             description = "[Click Here!](https://top.gg/bot/639498607632056321/vote)",
             color = discord.Color.green()
        )
        voteL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=voteL)
    
    @commands.command(name="invite", aliases=["invitelink"])
    async def inviteLink(self, ctx):
        invL = discord.Embed(
             title = "Add Villager Bot to your server",
             description = "[Click Here!](https://bit.ly/2tQfOhW)",
             color = discord.Color.green()
        )
        invL.set_thumbnail(url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=invL)
        
    @commands.command(name="google")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def googleSearch(self, ctx):
        query = ctx.message.clean_content[9:]
        if query == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to actually tell me what to search for, idiot."))
            return
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
    async def ytSearch(self, ctx):
        query = ctx.message.clean_content[10:]
        if query == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to actually tell me what to search for, idiot."))
            return
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
    async def redditSearch(self, ctx):
        query = ctx.message.clean_content[9:]
        if query == "":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to actually tell me what to search for, idiot."))
            return
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