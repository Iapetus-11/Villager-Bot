from discord.ext import commands
import discord
from random import choice
import json


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        self.leaderboard = [('0', '-1',), ('0', '-1',), ('0', '-1',), ('0', '-1',), ('0', '-1',), ('0', '-1',), ('0', '-1',),
                            ('0', '-1',), ('0', '-1',), ('0', '-1',)]

    @commands.command(name="ownerhelp", aliases=["helpowner", "owner"])
    @commands.is_owner()
    async def ownerhelp(self, ctx):
        embedMsg = discord.Embed(
            description="""
**{0}unload** ***cog*** *unloads a cog*
**{0}load** ***cog*** *loads a cog*
**{0}reload** ***cog*** *reloads a cog, error if cog had not been loaded prior*

**{0}activity** ***text*** *sets activity of bot to given text*
**{0}nextactivity** *picks random activity from list*

**{0}guilds** *lists guild member count, guild name, guild id*
**{0}dms** *lists private channels (group msgs and dms)*
**{0}leaveguild** ***guild id*** *leaves specified guild*
**{0}getinvites** ***guild id*** *gets invite codes for specified guild*

**{0}info2** *displays information about stuff*
**{0}cogs** *lists the loaded cogs*
**{0}reverselookup** ***user*** *shows what servers a user is in*

**{0}setbal** ***@user amount*** *set user balance to something*
**{0}setvault** ***@user amount*** *set user's vault to given amount*
**{0}getvault** ***@user*** *gets the mentioned user's vault*
**{0}setpickaxe** ***user*** ***pickaxe type*** *sets pickaxe level of a user*

**{0}eval** ***statement*** *uses eval()*
**{0}awaiteval** ***statement*** *uses await eval()*

**{0}botban** ***user*** *bans a user from using the bot*
**{0}botunban** ***user*** *unbans a user from using the bot*

**{0}addtoplaying** ***text*** *add a status to the list of statuses cycled through by the bot*
**{0}addtocursed** ***image*** *add an image to the list of cursed images used in the !!cursed command*
**{0}addmcserver** ***ip port "version" type verified \*note*** *adds to the list of mc servers*

**{0}restart** *forcibly restarts the bot*
""".format(ctx.prefix), color=discord.Color.green())
        embedMsg.set_author(name="Villager Bot Owner Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=embedMsg)

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension("cogs." + cog)
        except Exception as e:
            await ctx.send("Error while unloading extension: {0}\n``{1}``".format(cog, e))
            return
        await ctx.send(f"Successfully unloaded cog: " + cog)

    @commands.command(name="load")
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension("cogs." + cog)
        except Exception as e:
            await ctx.send("Error while loading extension: {0}\n``{1}``".format(cog, e))
            return
        await ctx.send("Successfully loaded cog: " + cog)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.reload_extension("cogs." + cog)
        except Exception as e:
            await ctx.send("Error while reloading extension: {0}\n``{1}``".format(cog, e))
            return
        await ctx.send("Successfully reloaded cog: " + cog)

    @commands.command(name="botban")
    @commands.is_owner()
    async def botban(self, ctx, user: discord.User):
        ban = await self.db.botBan(user.id)
        await ctx.send(ban.format(str(user)))

    @commands.command(name="botunban")
    @commands.is_owner()
    async def botunban(self, ctx, user: discord.User):
        unban = await self.db.botUnban(user.id)
        await ctx.send(unban.format(str(user)))

    @commands.command(name="botbans")
    @commands.is_owner()
    async def listbotbans(self, ctx):
        bans = await self.db.listBotBans()
        if len(bans) < 1:
            await ctx.send("No one has been banned from the bot yet")
            return
        for ban in bans:
            await ctx.send(f"{self.bot.get_user(int(ban[0]))} *{ban[0]}*")

    @commands.command(name="activity")
    @commands.is_owner()
    async def activity(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.bot.change_presence(activity=discord.Game(name=message))

    @commands.command(name="nextactivity")
    @commands.is_owner()
    async def nextactivity(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))

    @commands.command(name="guilds")
    @commands.is_owner()
    async def guilds(self, ctx):
        i = 0
        rows = 35
        msg = ""
        for guild in self.bot.guilds:
            i += 1
            msg += f"\n{guild.member_count} **{guild.name}** *{guild.id}*"
            if i % rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

    @commands.command(name="dms")
    @commands.is_owner()
    async def dmlist(self, ctx):
        i = 0
        rows = 30
        msg = ""
        for pchannel in self.bot.private_channels:
            i += 1
            try:
                msg += f"\n*{pchannel.id} + *  {pchannel}"
            except Exception as e:
                msg += "\n" + str(e)
            if i % rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

    @commands.command(name="leaveguild")
    @commands.is_owner()
    async def leaveguild(self, ctx, *, guild: int):
        await self.bot.get_guild(guild).leave()

    @commands.command(name="getinvites")
    @commands.is_owner()
    async def getinvites(self, ctx, *, guild: int):
        invites = await self.bot.get_guild(guild).invites()
        i = 0
        rows = 30
        msg = ""
        for invite in invites:
            i += 1
            msg += "\n" + str(invite.code)
            if i % rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

    @commands.command(name="info2")
    @commands.is_owner()
    async def info2(self, ctx):
        infoEmbed = discord.Embed(description="", color=discord.Color.green())
        infoEmbed.add_field(name="__**Owner Info**__", value=f"""
Guild Count: {len(self.bot.guilds)}
DM Channel Count: {len(self.bot.private_channels)}
User Count: {len(self.bot.users)}
Session Message Count: {self.g.msg_count}
Session Command Count: {self.g.cmd_count} ({round((self.g.cmd_count/self.g.msg_count)*100, 2)}% of all msgs)
Average Commands/Sec: {round(self.g.cmd_vect/30, 2)}
Shard Count: {self.bot.shard_count}
Latency: {round(self.bot.latency*1000, 2)} ms
""")
        await ctx.send(embed=infoEmbed)

    @commands.command(name="eval")
    @commands.is_owner()
    async def evalMessage(self, ctx, *, msg):
        try:
            evalMsg = eval(msg)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(evalMsg)))
        except Exception as e:
            if type(e) == discord.HTTPException:
                if e.code == 50035:
                    with open("data/eval.txt", "w+") as evalF:
                        evalF.write(str(evalMsg))
                    with open("data/eval.txt", "r") as evalF:
                        await ctx.send(file=discord.File(evalF))
                    with open("data/eval.txt", "w+") as evalF:
                        evalF.write("None")
                else:
                    await ctx.send(str(e))
            else:
                await ctx.send(str(e))

    @commands.command(name="awaiteval")
    @commands.is_owner()
    async def awaitEvalMessage(self, ctx, *, msg):
        try:
            evalMsg = await eval(msg)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(evalMsg)))
        except Exception as e:
            if type(e) == discord.HTTPException:
                if e.code == 50035:
                    with open("data/eval.txt", "w+") as evalF:
                        evalF.write(str(evalMsg))
                    with open("data/eval.txt", "r") as evalF:
                        await ctx.send(file=discord.File(evalF))
                else:
                    await ctx.send(str(e))
            else:
                await ctx.send(str(e))

    @commands.command(name="setpickaxe", aliases=["setpick"])
    @commands.is_owner()
    async def setpick(self, ctx, user: discord.User, pType: str):
        await self.db.setPick(user.id, pType)

    @commands.command(name="reverselookup", aliases=["lookup"])
    @commands.is_owner()
    async def inverseguildlookup(self, ctx, user: discord.User):
        gds = ""
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id == user.id:
                    gds += str(guild) + " **|** " + str(guild.id) + "\n"
        if not gds == "":
            await ctx.send(gds)
        else:
            await ctx.send("No results...")

    @commands.command(name="cogs")
    @commands.is_owner()
    async def listCogs(self, ctx):
        for ext in list(self.bot.extensions):
            await ctx.send(ext)

    @commands.command(name="setbal")
    @commands.is_owner()
    async def balset(self, ctx, user: discord.User, amount: int):
        await self.db.setBal(user.id, amount)

    @commands.command(name="getvault")
    @commands.is_owner()
    async def getvault(self, ctx, user: discord.User):
        vault = await self.db.getVault(user.id)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=user.display_name + "'s vault: " + str(vault[0]) + "<:emerald_block:679121595150893057>/" + str(vault[1])))

    @commands.command(name="setvault")
    @commands.is_owner()
    async def setvault(self, ctx, user: discord.User, amount: int, maxx: int):
        await self.db.setVault(user.id, amount, maxx)

    @commands.command(name="addtoplaying")
    @commands.is_owner()
    async def addtoplaying(self, ctx, *, new: str):
        self.g.playingList.append(new)
        with open("data/playing_list.json", "w+") as playingList:
            playingList.write(json.dumps(self.g.playingList))
        await ctx.send(f"Added {new} to the \"Playing\" list.")

    @commands.command(name="addtocursed")
    @commands.is_owner()
    async def addtocursed(self, ctx, *, new: str):
        self.g.cursedImages.append(new)
        with open("data/cursed_images.json", "w+") as cursedImages:
            playingList.write(json.dumps(self.g.cursedImages))
        await ctx.send(f"Added {new} to the cursed images list")

    @commands.command(name="addmcserver")
    @commands.is_owner()
    async def addmcserver(self, ctx, ip: str, port: int, version: str, typp: str, verified: bool, *, note: str):
        server = {"ip": ip, "port": port, "version": version, "type": typp, "verified": verified, "note": note}
        self.g.mcServers.append(server)
        with open("data/minecraft_servers.json", "w+") as mcServers:
            mcServers.write(json.dumps(self.g.mcServers))
        await ctx.send(f"Added {str(server)} to the Minecraft server list")\
              
    @commands.command(name="restart")
    @commands.is_owner()
    async def reeeeeeeeee(self, ctx):
        await ctx.send("Force restarting le bot...")
        self.db.db.close()
        exit()


def setup(bot):
    bot.add_cog(Owner(bot))
