from discord.ext import commands
import discord
import arrow
from random import choice
import async_cse
import json


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")

        with open("data/keys.json", "r") as keys:
            self.google = async_cse.Search(json.load(keys)["googl"])

    def cog_unload(self):
        self.bot.loop.create_task(self.google.close())

    @commands.group(name="help")
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            help_embed = discord.Embed(color=discord.Color.green())
            help_embed.set_author(
                name="Villager Bot Commands",
                icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

            help_embed.add_field(name="Minecraft", value=f"``{ctx.prefix}help mc``", inline=True)
            help_embed.add_field(name="Fun", value=f"``{ctx.prefix}help fun``", inline=True)
            help_embed.add_field(name="\uFEFF", value=f"\uFEFF", inline=True)
            help_embed.add_field(name="Useful", value=f"``{ctx.prefix}help useful``", inline=True)
            help_embed.add_field(name="Admin", value=f"``{ctx.prefix}help admin``", inline=True)
            help_embed.add_field(name="\uFEFF", value=f"\uFEFF", inline=True)
            help_embed.add_field(name="\uFEFF", value="""Need more help? Check out the Villager Bot [Support Server](https://discord.gg/39DwwUV)
            Enjoying the bot? Vote for us on [top.gg](https://top.gg/bot/639498607632056321/vote)""", inline=False)
            help_embed.set_footer(text="Need more help? Check out the support server: discord.gg/39DwwUV")
            await ctx.send(embed=help_embed)

    @help.command(name='fun')
    async def help_fun(self, ctx):

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
            f'**{ctx.prefix}say** ***text*** *bot will repeat what you tell it to*\n'
            f'**{ctx.prefix}bubblewrap** *bot will send some bubble wrap for you to pop*\n'
            f'**{ctx.prefix}clap** ***text*** *:clap: bot :clap: will :clap: send :clap: text :clap: like :clap: this :clap:*\n',
            inline=False)

        help_embed.add_field(
            name="**Economy Commands**",
            value=f'**{ctx.prefix}mine** *go mining with the bot for emeralds*\n'
f'**{ctx.prefix}balance** *the bot will tell you how many emeralds you have*\n'
f'**{ctx.prefix}vault** *shows you how many emerald blocks you have in the emerald vault*\n'
f'**{ctx.prefix}deposit** ***amount in emerald blocks*** *deposit emerald blocks into the emerald vault*\n'
f'**{ctx.prefix}withdraw** ***amount in emerald blocks*** *withdraw emerald blocks from the emerald vault*\n'
f'**{ctx.prefix}inventory** *see what you have in your inventory*\n'
f'**{ctx.prefix}give** ***@user amount*** ***[optional: item]*** *give mentioned user emeralds or an item*\n'
f'**{ctx.prefix}gamble** ***amount*** *gamble with Villager Bot*\n', inline=False)
        help_embed.add_field(
            name="**More Economy Commands**",
            value=f'**{ctx.prefix}pillage** ***@user*** *attempt to steal emeralds from another person*\n'
f'**{ctx.prefix}shop** *go shopping with emeralds*\n'
f'**{ctx.prefix}sell** ***amount item*** *sell a certain amount of an item*\n'
f'**{ctx.prefix}leaderboard** *shows the available leaderboards*\n'
f'**{ctx.prefix}chug** ***potion*** *uses the mentioned potion.*\n'
f'**{ctx.prefix}honey** *apparently bees produce honey, who knew it could sell for emeralds*\n',
            inline=False)

        help_embed.add_field(
            name="**Other Fun Commands**",
            value=f'**{ctx.prefix}cursed** *the bot will upload a cursed Minecraft image*\n'
                  f'**{ctx.prefix}battle** ***user*** *allows you to battle your friends!*\n'
                  f'**{ctx.prefix}kill** ***user*** *kills the mentioned user*\n',
            inline=False)

        help_embed.set_footer(text="Need more help? Check out the support server: discord.gg/39DwwUV")

        await ctx.send(embed=help_embed)

    @help.command(name='useful')
    async def help_useful(self, ctx):

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
            f'**{ctx.prefix}image** ***query*** *bot will search google images for your query*\n'
            f'**{ctx.prefix}stats** *shows the bot\'s stats*\n'
            f'**{ctx.prefix}math** ***math*** *does math*\n',
            inline=True)

        help_embed.set_footer(text="Need more help? Check out the support server: discord.gg/39DwwUV")

        await ctx.send(embed=help_embed)

    @help.command(name='admin')
    async def help_admin(self, ctx):

        help_embed = discord.Embed(color=discord.Color.green())
        help_embed.set_author(
            name="Villager Bot Commands",
            icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

        help_embed.add_field(
            name="**Admin Only**",
            value=f'**{ctx.prefix}config** *change the settings of the bot for your server*\n'
            f"**{ctx.prefix}purge** ***number of messages*** *deletes n number of messages where it's used*\n"
            f'**{ctx.prefix}kick** ***@user*** *kicks the mentioned user*\n'
            f'**{ctx.prefix}ban** ***@user*** *bans the mentioned user*\n'
            f'**{ctx.prefix}pardon** ***@user*** *unbans the mentioned user*\n'
            f'**{ctx.prefix}warn** ***@user reason*** *warns the mentioned user*\n'
            f'**{ctx.prefix}warns** ***@user*** *shows the mentioned user\'s warnings*\n'
            f'**{ctx.prefix}clearwarns** ***@user*** *clears the mentioned user\'s warnings*\n',
            inline=True)

        help_embed.set_footer(text="Need more help? Check out the support server: discord.gg/39DwwUV")

        await ctx.send(embed=help_embed)
        
    @help.command(name="mc")
    async def help_mc(self, ctx):

        help_embed = discord.Embed(color=discord.Color.green())
        help_embed.set_author(
            name="Villager Bot Commands",
            icon_url="http://172.10.17.177/images/villagerbotsplash1.png")

        help_embed.add_field(
            name="**Minecraft Commands**",
            value=f'**{ctx.prefix}mcping** ***ip:port*** *to check the status of a Java Edition Minecraft server*\n'
            f'**{ctx.prefix}mcpeping** ***ip*** *to check the status of a Bedrock Edition Minecraft server*\n'
            f'**{ctx.prefix}stealskin** ***gamertag*** *steal another player\'s Minecraft skin*\n'
            f'**{ctx.prefix}nametouuid** ***gamertag*** *gets the Minecraft uuid of the given player*\n'
            f'**{ctx.prefix}uuidtoname** ***uuid*** *gets the gamertag from the given Minecraft uuid*\n'
            f'**{ctx.prefix}randommc** *sends a random Minecraft server*\n'
            f'**{ctx.prefix}buildidea** *sends a random idea on what you could build*\n'
            f'**{ctx.prefix}colorcodes** *sends a Minecraft color code cheat-sheet your way.*\n',
            inline=True)

        help_embed.set_footer(text="Need more help? Check out the support server: discord.gg/39DwwUV")

        await ctx.send(embed=help_embed)

    @commands.command(name="info", aliases=["information"])
    async def information(self, ctx):
        info_msg = discord.Embed(color=discord.Color.green())
        info_msg.add_field(name="Command Prefix", value=ctx.prefix, inline=True)
        info_msg.add_field(name="Bot Library", value="Discord.py", inline=True)
        info_msg.add_field(name="Creators", value="Iapetus11#6821 &\n TrustedMercury#1953", inline=True)
        info_msg.add_field(name="Total Servers", value=str(len(self.bot.guilds)), inline=True)
        info_msg.add_field(name="Shards", value=str(self.bot.shard_count), inline=True)
        info_msg.add_field(name="Total Users", value=str(len(self.bot.users)), inline=True)
        info_msg.add_field(name="Top.gg Page", value="[Click Here](https://top.gg/bot/639498607632056321)", inline=True)
        info_msg.add_field(name="Website", value="[Click Here](https://villagerbot.xyz)", inline=True)
        info_msg.add_field(name="Discord", value="[Click Here](https://discord.gg/39DwwUV)", inline=True)
        info_msg.set_author(name="Villager Bot Information", icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=info_msg)

    @commands.command(name="ping", aliases=["pong", "ding", "dong", "shing", "shling", "schlong"]) # Checks latency between Discord API and the bot
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
        elif "shing" in c or "shling" in c:
            pp = "Schlong"
        elif "schlong" in c:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"<a:ping:692401875001278494> Magnum Dong! \uFEFF ``{69.00} ms``"))
            return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"<a:ping:692401875001278494> {pp}! \uFEFF ``{round(self.bot.latency*1000, 2)} ms``"))

    @commands.command(name="uptime")
    async def get_uptime(self, ctx):
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
    async def vote_link(self, ctx):
        _vote_link = discord.Embed(description="[**Click Here!**](https://top.gg/bot/639498607632056321/vote)", color=discord.Color.green())
        _vote_link.set_author(name="Vote for Villager Bot", icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=_vote_link)

    @commands.command(name="invite", aliases=["invitelink"])
    async def invite_link(self, ctx):
        inv_l = discord.Embed(description="[**Click Here!**](https://bit.ly/2tQfOhW)", color=discord.Color.green())
        inv_l.set_author(name="Add Villager Bot to your server", icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=inv_l)

    @commands.command(name="google")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def google_search(self, ctx, *, query: str):
        await ctx.trigger_typing()
        try:
            rez = (await self.google.search(query, safesearch=True)) # Grab only first result
        except async_cse.search.NoResults:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for that query!"))
            return
        except async_cse.search.APIError:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh Oh, there was an error, please try again later!"))
            return
        if len(rez) == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for that query!"))
            return
        rez = rez[0]
        embed = discord.Embed(color=discord.Color.green(), title=rez.title, description=rez.description, url=rez.url)
        await ctx.send(embed=embed)

    @commands.command(name="youtube")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def youtube_search(self, ctx, *, query: str):
        await ctx.trigger_typing()
        try:
            results = (await self.google.search(query, safesearch=True))
        except async_cse.search.NoResults:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for that query!"))
            return
        except async_cse.search.APIError:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh Oh, there was an error, please try again later!"))
            return
        rez = None
        for result in results:
            if "youtube" in result.url:
                rez = result
                break
        if rez is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for that query!"))
        else:
            embed = discord.Embed(color=discord.Color.green(), title=rez.title, description=rez.description, url=rez.url)
            embed.set_thumbnail(url=rez.image_url)
            await ctx.send(embed=embed)

    @commands.command(name="image", aliases=["imagesearch"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def image_search(self, ctx, *, query: str):
        await ctx.trigger_typing()
        try:
            results = (await self.google.search(query, safesearch=True, image_search=True))
        except async_cse.search.NoResults:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for that query!"))
            return
        except async_cse.search.APIError:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh Oh, there was an error, please try again later!"))
            return
        embed = discord.Embed(color=discord.Color.green())
        try:
            embed.set_image(url=results[0].image_url)
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"[Result for \"{query}\"]({results[0].image_url})"))

    @commands.command(name="nsfwimage", aliases=["nsfwimagesearch", "nsfw"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def nsfw_image_search(self, ctx, *, query: str):
        if not isinstance(ctx.channel, discord.DMChannel):
            if not ctx.channel.is_nsfw():
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Hey, there are kids here! You can only use this command in nsfw channels!"))
                return
        await ctx.trigger_typing()
        try:
            results = (await self.google.search(query, safesearch=False, image_search=True))
        except async_cse.search.NoResults:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="No results found for that query!"))
            return
        except async_cse.search.APIError:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Uh Oh, there was an error, please try again later!"))
            return
        image = choice(results)
        embed = discord.Embed(color=discord.Color.green())
        embed.set_image(url=choice(results).image_url)
        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def info_2(self, ctx):
        desc = f"Guild Count: ``{len(self.bot.guilds)}``\n" \
               f"DM Channel Count: ``{len(self.bot.private_channels)}``\n" \
               f"User Count: ``{len(self.bot.users)}``\n" \
               f"Session Message Count: ``{self.g.msg_count}``\n" \
               f"Session Command Count: ``{self.g.cmd_count} ({round((self.g.cmd_count/self.g.msg_count)*100, 2)}% of all msgs)``\n" \
               f"Commands/Sec: ``{self.g.cmd_vect[1]}``\n" \
               f"Session Vote Count: ``{self.g.vote_count}``\n" \
               f"Top.gg Votes/Hour: ``{self.g.vote_vect[1]}``\n" \
               f"Shard Count: ``{self.bot.shard_count}``\n" \
               f"Latency: ``{round(self.bot.latency*1000, 2)} ms``\n"

        info_embed = discord.Embed(color=discord.Color.green(), description=desc)
        info_embed.set_author(name="Villager Bot Statistics", icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=info_embed)

    @commands.command(name="math")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def do_math(self, ctx):
        try:
            problem = str(ctx.message.clean_content.replace(f"{ctx.prefix}math", ""))
            if problem == "":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You actually have to put in a problem, idiot."))
                return
            if len(problem) > 500:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That's a bit too long, don't you think?"))
                return
            problem = problem.replace("÷", "/").replace("x", "*").replace("•", "*").replace("=", "==").replace("π", "3.14159")
            for letter in "abcdefghijklmnopqrstuvwxyz\\_@~`,<>?|'\"{}[]":
                if letter in problem:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That math problem contains invalid characters, please try again."))
                    return
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"```{str(round(eval(problem), 4))}```"))
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Oops, something went wrong."))


def setup(bot):
    bot.add_cog(Useful(bot))
