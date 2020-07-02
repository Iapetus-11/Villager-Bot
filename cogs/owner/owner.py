import arrow
import asyncio
import discord
import json
import resource
from discord.ext import commands
from os import system
from random import choice
from time import sleep


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")
        self.emerald = "<:emerald:653729877698150405>"

    @commands.command(name="ownerhelp", aliases=["helpowner", "owner"])
    async def owner_help(self, ctx):
        embed_msg = discord.Embed(
            description="""
**{0}unload** ***cog*** *unloads a cog*
**{0}load** ***cog*** *loads a cog*
**{0}reload** ***cog*** *reloads a cog, error if cog had not been loaded prior*

**{0}guilds** *lists guild member count, guild name, guild id*
**{0}dms** *lists private channels (group msgs and dms)*
**{0}leaveguild** ***guild id*** *leaves specified guild*
**{0}getinvites** ***guild id*** *gets invite codes for specified guild*
**{0}lookup** ***user*** *shows what servers a user is in*
**{0}seedm** ***user id*** ***msg count*** *shows dm*

**{0}reeeee** *reeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee*
**{0}cogs** *lists the loaded cogs*
**{0}getgiveaway** ***message id*** *gets two winners from the specified message, uses first reaction on specified message*

**{0}setbal** ***@user amount*** *set user balance to something*
**{0}setvault** ***@user amount*** *set user's vault to given amount*
**{0}getvault** ***@user*** *gets the mentioned user's vault*
**{0}setpickaxe** ***user*** ***pickaxe type*** *sets pickaxe level of a user*
**{0}resetprefix** ***guild id*** *resets the prefix of a server*
**{0}clearvotes** *clears vote tracker*
**{0}votegiveawayget** *gets a winner from the vote tracker*
""".format(ctx.prefix), color=discord.Color.green())
        embed_msg.set_author(name="Villager Bot Owner Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=embed_msg)
        embed_msg = discord.Embed(
            description="""
**{0}botban** ***user*** *bans a user from using the bot*
**{0}botbanmulti** ***[users]*** *bot-bans the list of users*
**{0}banmulti** ***[users]*** *bans the list of users from the current server*
**{0}botbans** *lists the bot bans*
**{0}botunban** ***user*** *unbans a user from using the bot*

**{0}activity** ***text*** *sets activity of bot to given text*
**{0}nextactivity** *picks random activity from list*
**{0}addtoplaying** ***text*** *add a status to the list of statuses cycled through by the bot*
**{0}addtocursed** ***image*** *add an image to the list of cursed images used in the !!cursed command*
**{0}addmcserver** ***ip port "version" type verified \*note*** *adds to the list of mc servers*
**{0}reloaditems** *reload the list of items from the json file*
**{0}reloadshopitems** *reload shop items*

**{0}eval** ***statement*** *uses eval()*
**{0}awaiteval** ***statement*** *uses await eval()*
**{0}getlatest** *pulls latest from github*
**{0}backupdb** *backs up the db*
**{0}updateroles** *does roles idk bro*
**{0}testblocking** *intentionally blocks code*
**{0}dumpserverlist** *dumps the server list into a text file and uploads it*
""".format(ctx.prefix), color=discord.Color.green())
        embed_msg.set_author(name="More Villager Bot Owner Commands", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        await ctx.send(embed=embed_msg)

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension("cogs." + cog)
        except Exception as e:
            await ctx.send(f"Error while unloading extension: {cog}\n``{e}``")
            return
        await ctx.send(f"Successfully unloaded cog: " + cog)

    @commands.command(name="load")
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension("cogs." + cog)
        except Exception as e:
            await ctx.send(f"Error while loading extension: {cog}\n``{e}``")
            return
        await ctx.send("Successfully loaded cog: " + cog)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.reload_extension("cogs." + cog)
        except Exception as e:
            await ctx.send(f"Error while reloading extension: {cog}\n``{e}``")
            return
        await ctx.send("Successfully reloaded cog: " + cog)

    @commands.command(name="botban")
    @commands.is_owner()
    async def _bot_ban(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            await ctx.send("You can't bot ban yourself!")
            return
        if user.id == 536986067140608041:
            await ctx.send("lol get recked u just banned urself retard")
            user = ctx.author
        ban = await self.db.ban_from_bot(user.id)
        await ctx.send(ban.format(str(user)))

    @commands.command(name="multibotban", aliases=["botbanmulti"])
    @commands.is_owner()
    async def _bot_ban_multi(self, ctx, *, users: str):
        user_list = eval(users)
        for user in user_list:
            await self.db.ban_from_bot(user)
        await ctx.send(f"Bot-banned {len(user_list)} users.")

    @commands.command(name="banmulti", aliases=["multiban", "manyban", "banmany"])
    @commands.is_owner()
    async def ban_multi(self, ctx, *, users: str):
        user_list = eval(users)
        for user in user_list:
            member = ctx.guild.get_member(user)
            if member is not None:
                await member.ban(reason="Multiban")
        await ctx.send(f"Banned {len(user_list)} members.")

    @commands.command(name="botunban")
    @commands.is_owner()
    async def _bot_unban(self, ctx, user: discord.User):
        unban = await self.db.unban_from_bot(user.id)
        await ctx.send(unban.format(str(user)))

    @commands.command(name="botbans")
    @commands.is_owner()
    async def list_bot_bans(self, ctx):
        bans = await self.db.list_bot_bans()
        if len(bans) < 1:
            await ctx.send("No one has been banned from the bot yet")
            return
        for ban in bans:
            await ctx.send(f"{self.bot.get_user(int(ban[0]))} *{ban[0]}*")

    @commands.command(name="activity", aliases=["setactivity"])
    @commands.is_owner()
    async def activity(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.bot.change_presence(activity=discord.Game(name=message))

    @commands.command(name="nextactivity")
    @commands.is_owner()
    async def next_activity(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))

    @commands.command(name="guilds")
    @commands.is_owner()
    async def guild_list(self, ctx):
        i = 0
        rows = 35
        msg = ""
        for guild in self.bot.guilds:
            i += 1
            msg += f"\n{guild.member_count} **{discord.utils.escape_markdown(guild.name)}** *{guild.id}*"
            if i % rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

    @commands.command(name="dms")
    @commands.is_owner()
    async def dm_list(self, ctx):
        i = 0
        rows = 30
        msg = ""
        for private_channel in self.bot.private_channels:
            i += 1
            try:
                msg += f"\n*{private_channel.id}*  {discord.utils.escape_markdown(str(private_channel))}"
            except Exception as e:
                msg += "\n" + str(e)
            if i % rows == 0:
                await ctx.send(msg)
                msg = ""
        if msg is not "":
            await ctx.send(msg)

    @commands.command(name="leaveguild")
    @commands.is_owner()
    async def leave_guild(self, ctx, *, guild: int):
        await self.bot.get_guild(guild).leave()

    @commands.command(name="getinvites")
    @commands.is_owner()
    async def get_invites(self, ctx, *, guild: int):
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

    @commands.command(name="eval")
    @commands.is_owner()
    async def eval_message(self, ctx, *, msg):
        await ctx.send(f"{eval(msg)}\uFEFF")

    @commands.command(name="awaiteval")
    @commands.is_owner()
    async def await_eval_message(self, ctx, *, msg):
        await ctx.send(f"{await eval(msg)}\uFEFF")

    @commands.command(name="setpickaxe", aliases=["setpick"])
    @commands.is_owner()
    async def setpick(self, ctx, user: discord.User, pType: str):
        await self.db.set_pickaxe(user.id, pType)
        await self.bot.get_cog("Econ").update_user_role(user.id)
        await ctx.send(f"Set {user}'s pickaxe to {pType}.")

    @commands.command(name="reverselookup", aliases=["lookup"])
    @commands.is_owner()
    async def guild_lookup(self, ctx, user: discord.User):
        gds = ""
        for guild in self.bot.guilds:
            if guild.get_member(user.id) is not None:
                gds += str(guild) + " **|** " + str(guild.id) + "\n"
        if not gds == "":
            await ctx.send(gds)
        else:
            await ctx.send("No results...")

    @commands.command(name="cogs")
    @commands.is_owner()
    async def list_cogs(self, ctx):
        for ext in list(self.bot.extensions):
            await ctx.send(ext)

    @commands.command(name="setbal")
    @commands.is_owner()
    async def set_bal(self, ctx, user: discord.User, amount: int):
        await self.db.set_balance(user.id, amount)
        await ctx.send(f"Set {user}'s balance to {amount}.")

    @commands.command(name="getvault")
    @commands.is_owner()
    async def get_vault(self, ctx, user: discord.User):
        vault = await self.db.get_vault(user.id)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description=user.display_name + "'s vault: " + str(vault[0]) + "<:emerald_block:679121595150893057>/" + str(vault[1])))

    @commands.command(name="setvault")
    @commands.is_owner()
    async def set_vault(self, ctx, user: discord.User, amount: int, maxx: int):
        await self.db.set_vault(user.id, amount, maxx)
        await ctx.send(f"Set {user}'s vault to {amount} {maxx}.")

    @commands.command(name="addtoplaying")
    @commands.is_owner()
    async def add_to_playing(self, ctx, *, new: str):
        self.g.playingList.append(new)
        with open("data/playing_list.json", "w+") as playingList:
            playingList.write(json.dumps(self.g.playingList))
        await ctx.send(f"Added {new} to the \"Playing\" list.")

    @commands.command(name="addtocursed")
    @commands.is_owner()
    async def add_to_cursed(self, ctx, *, new: str):
        self.g.cursedImages.append(new)
        with open("data/cursed_images.json", "w+") as cursedImages:
            cursedImages.write(json.dumps(self.g.cursedImages))
        await ctx.send(f"Added {new} to the cursed images list")

    @commands.command(name="addmcserver")
    @commands.is_owner()
    async def add_mc_server(self, ctx, ip: str, port: int, version: str, typp: str, verified: bool, *, note: str):
        server = {"ip": ip, "port": port, "version": version, "type": typp, "verified": verified, "note": note}
        self.g.mcServers.append(server)
        with open("data/minecraft_servers.json", "w+") as mcServers:
            mcServers.write(json.dumps(self.g.mcServers))
        await ctx.send(f"Added {str(server)} to the Minecraft server list")

    @commands.command(name="reloadshopitems", aliases=["reloadshop"])
    @commands.is_owner()
    async def reload_shop_items(self, ctx):
        with open("data/shop_items.json", "r") as shop_items:
            self.g.shop_items = json.load(shop_items)
        await ctx.send("Reloaded the shop items")

    @commands.command(name="getlatest", aliases=["gitpull", "git_pull"])
    @commands.is_owner()
    async def get_and_deploy_latest(self, ctx):
        system("git pull > git_pull_log 2>&1")
        with open("git_pull_log", "r") as f:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"```{f.read()}```")) # Maybe change the language of the ``` in the future for nice colors? idk
        system("rm git_pull_log")

    @commands.command(name="backupdb")
    @commands.is_owner()
    async def backup_database(self, ctx):
        system("pg_dump villagerbot | gzip > ../database-backups/{0}.gz".format(arrow.utcnow().ctime().replace(" ", "_").replace(":", ".")))
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Backed up the database!"))

    @commands.command(name="reloaditems")
    @commands.is_owner()
    async def reload_items(self, ctx):
        with open("data/items.json", "r") as items:
            self.g.items = json.load(items)
        await ctx.send("Reloaded the items list")

    @commands.command(name="resetprefix")
    @commands.is_owner()
    async def reset_prefix(self, ctx, gid: int):
        await self.db.drop_prefix(gid)
        await ctx.send(f"Reset the prefix for guild: {self.bot.get_guild(gid)}")

    @commands.command(name="updateroles")
    @commands.is_owner()
    async def do_roles(self, ctx):
        await ctx.send("Updating roles...")
        econ = self.bot.get_cog("Econ")
        for user in self.bot.get_guild(641117791272960031).members:
            await econ.update_user_role(user.id)
        await ctx.send("Done.")

    @commands.command(name="testblocking")
    @commands.is_owner()
    async def test_blocking(self, ctx):
        await ctx.send("Testing...")
        sleep(15)
        await ctx.send("Done.")

    @commands.command(name="getgiveaway")
    @commands.is_owner()
    async def get_giveaway_winners(self, ctx, message_id: int):
        msg = await ctx.guild.get_channel(644391543075242014).fetch_message(message_id)
        users = await msg.reactions[0].users().flatten()
        await ctx.send(f"Winners: {choice(users)} & {choice(users)}")

    @commands.command(name="reeeeeeee", aliases=["reeeeeee", "reeeeee", "reeeee", "reeee", "reee", "ree", "re", "r", "reeeeeeeee", "reeeeeeeeee", "reeeeeeeeeee", "reeeeeeeeeeee", "reeeeeeeeeeeee"])
    @commands.is_owner()
    async def reeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee(self, ctx):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(choice(["<:reeeeeee2:703802166900424754>", "<:reeeeeee3:703802166409691247>", "<:reeee:655577956831199254>", "<a:reeeeeee1:703802166439182357>", "<a:reeeee:655438580814053451>"]))

    @commands.command(name="seedm", aliases=["seedms", "dm"])
    @commands.is_owner()
    async def see_dm_channel(self, ctx, user: discord.User, msg_count: int = 10):
        if user.dm_channel is None:
            await user.create_dm()
        channel = user.dm_channel
        embed = discord.Embed(color=discord.Color.green(), description=f"DM with {channel.recipient}")
        channel_history = await channel.history(limit=msg_count).flatten()
        for message in channel_history[::-1]:
            if len(message.content) > 1024:
                embed.add_field(name=message.author, value="\uFEFF"+message.content[:1020], inline=True)
                embed.add_field(name="\uFEFF", value="\uFEFF"+message.content[1020:], inline=True)
            else:
                embed.add_field(name=message.author, value="\uFEFF"+message.content, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="memory", aliases=["ram", "mem"])
    @commands.is_owner()
    async def get_memory_usage(self, ctx):
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Memory in use: ``{round(mem*.001*1.04858, 2)} Megabytes``"))

    @commands.command(name="topten", aliases=["toptenguilds"]) # udj vri
    @commands.is_owner()
    async def top_ten(self, ctx):
        gds = self.bot.guilds
        gds.sort(reverse=True, key=lambda guild: guild.member_count)
        msg = ""
        for guild in gds[:10]:
            msg += f"**{guild.member_count}** {guild} *{guild.id}*\n"
        await ctx.send(msg)

    @commands.command(name="bigsteal", aliases=["stealbig", "bigbamboozle", "olswitcheroo"])
    @commands.is_owner()
    async def big_bamboozle(self, ctx):
        await ctx.send("Running...")
        _id = 333422871567400961
        ids = []
        count = 0
        for guild in self.bot.guilds:
            if guild.get_member(_id) is not None:
                await ctx.send(f"{guild.owner}")
                count += 1
        await ctx.send(f"Done! ({count})")

    @commands.command(name="whoyadaddy", aliases=["whoisowner", "iamowner", "whosyadaddy", "whoyadad", "whoyamaker"])
    @commands.is_owner()
    async def daddy(self, ctx):
        await ctx.send("Iapetus11 is 0_0")

    @commands.command(name="serverlistdump", aliases=["dumpservers", "dumpserverlist"])
    @commands.is_owner()
    async def dump_server_list(self, ctx):
        with open("server_list.txt", "w+") as f:
            f.write("\r\n".join([g.name for g in self.bot.guilds]))
        with open("server_list.txt", "r") as f:
            await ctx.send(file=discord.File(f, filename="servers.txt"))

    @commands.command(name="votegiveawayget", aliases=["votegiveawayend", "getvotewinner", "votewinner"])
    @commands.is_owner()
    async def get_vote_giveaway_winner(self, ctx):
        all = await self.db.vote_tracker_fetch_all()
        await ctx.send(self.bot.get_user(choice(all)[0]))

    @commands.command(name="clearvotetracker", aliases=["clearvotes"])
    @commands.is_owner()
    async def clear_vote_tracker(self, ctx):
        await self.db.vote_tracker_clear()
        await ctx.send("Done.")


def setup(bot):
    bot.add_cog(Owner(bot))
