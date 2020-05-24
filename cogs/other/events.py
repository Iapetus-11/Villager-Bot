from discord.ext import commands
import discord
from random import choice, randint
import asyncio
import logging
import dbl
import json
from math import ceil


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        with open("data/keys.json", "r") as k:
            keys = json.load(k)

        self.dblpy = dbl.DBLClient(self.bot, keys["dblpy"], webhook_path="/dblwebhook", webhook_auth=keys["dblpy2"],
                                   webhook_port=5000, autopost=True)

        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)

    def cog_unload(self):
        self.bot.loop.create_task(self.dblpy.close())

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name=choice(self.g.playingList)))
        self.logger.info(" Updated Activity")
        self.logger.info(f"\u001b[36;1m CONNECTED \u001b[0m [{self.bot.shard_count} Shards]")

    @commands.Cog.listener()
    async def on_guild_post(self):
        self.logger.info(" TOP.GG STATS UPDATED")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        self.logger.info("\u001b[35m DBL WEBHOOK TEST \u001b[0m")
        channel = self.bot.get_channel(643648150778675202)
        await channel.send(embed=discord.Embed(color=discord.Color.green(), description="DBL WEBHOOK TEST"))

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        self.g.vote_vect[0] += 1
        self.g.vote_count += 1
        user_id = int(data["user"])
        self.logger.info(f"\u001b[32;1m {user_id} VOTED ON TOP.GG \u001b[0m")
        user = self.bot.get_user(user_id)
        if user is not None:
            await self.bot.get_channel(682195105784004610).send(
                f":tada::tada: {discord.utils.escape_markdown(user.display_name)} has voted! :tada::tada:")
            multi = 1  # normally is 1
            if await self.dblpy.get_weekend_status():
                multi = 2  # normally is 2
            messages = ["You have been awarded {0}<:emerald:653729877698150405> for voting for Villager Bot!",
                        "You have received {0}<:emerald:653729877698150405> for voting for Villager Bot!",
                        "You have received {0}<:emerald:653729877698150405> because you voted for Villager Bot!"]
            try:
                await user.send(
                    embed=discord.Embed(color=discord.Color.green(), description=choice(messages).format(32 * multi)))
            except discord.errors.Forbidden:
                pass
            await self.db.set_balance(user_id, await self.db.get_balance(user_id) + (32 * multi))
        else:
            await self.bot.get_channel(682195105784004610).send(":tada::tada: An unknown user voted for the bot! :tada::tada:")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(1)
        if guild.system_channel is not None:
            try:
                await guild.system_channel.send(embed=discord.Embed(color=discord.Color.green(),
                                                                    description="Hey ya'll, type ``!!help`` to get started with Villager Bot!\n\n"
                                                                                "Want to receive updates, report a bug, or make suggestions? "
                                                                                "Join the official [support server](https://discord.gg/39DwwUV)!"))
            except discord.errors.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.db.drop_prefix(guild.id)
        await self.db.drop_do_replies(guild.id)
        await self.db.drop_do_tips(guild.id)


def setup(bot):
    bot.add_cog(Events(bot))
