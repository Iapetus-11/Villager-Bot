from discord.ext import commands
import discord
from random import choice
import asyncio
import logging
import dbl
import json


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        with open("data/keys.json", "r") as k:
            keys = json.load(k)

        self.dblpy = dbl.DBLClient(self.bot, keys["dblpy"], webhook_path='/dblwebhook', webhook_auth=keys["dblpy2"], webhook_port=5000)

        self.logger = logging.getLogger("Events")
        self.logger.setLevel(logging.INFO)

    def cog_unload(self):
        self.bot.loop.run_until_complete(self.stop_dblpy())

    async def stop_dblpy(self):
        await self.dblpy.close()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("\u001b[36;1m CONNECTED \u001b[0m")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        self.logger.info("\u001b[35m DBL WEBHOOK TEST \u001b[0m")
        channel = self.bot.get_channel(643648150778675202)
        await channel.send(embed=discord.Embed(color=discord.Color.green(), description="DBL WEBHOOK TEST"))

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        userID = int(data["user"])
        self.logger.info(f"\u001b[32;1m {userID} VOTED ON TOP.GG \u001b[0m")
        multi = 1
        if await self.dblpy.get_weekend_status():
            multi = 2
        await self.db.set_balance(userID, await self.db.get_balance(userID) + (32 * multi))
        user = self.bot.get_user(userID)
        if user is not None:
            await self.bot.get_channel(682195105784004610).send(f":tada::tada: {user.display_name} has voted! :tada::tada:")
            if choice([True, False]):
                for c in self.g.items:
                    if randint(0, c[2]) == c[3]:
                        e = "<:emerald:653729877698150405>"
                        try:
                            await ctx.send(choice([f"You {choice(['found', 'got'])} a {c[0]} (Worth {c[1]}{e}) for voting for Villager Bot!",
                                                   f"You {choice(['found', 'got'])} a {c[0]} (Worth {c[1]}{e}) because you voted for Villager Bot!",]))
                        except discord.errors.Forbidden:
                            pass
                        await self.db.add_item(ctx.author.id, c[0], 1, c[1])
                        return
            messages = ["You have been awarded {0}<:emerald:653729877698150405> for voting for Villager Bot!", "You have received {0}<:emerald:653729877698150405> for voting for Villager Bot!",
                        "You have received {0}<:emerald:653729877698150405> because you voted for Villager Bot!", "You have gotten {0}<:emerald:653729877698150405> because you voted for Villager Bot!"]
            try:
                await user.send(embed=discord.Embed(color=discord.Color.green(), description=choice(messages).format(32*multi)))
            except discord.errors.Forbidden:
                pass
        else:
            await self.bot.get_channel(682195105784004610).send(":tada::tada: An unknown user voted for the bot! :tada::tada:")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(1)
        ret = False
        i = 0
        join_msg = discord.Embed(color=discord.Color.green(), description="Hey ya'll, type **!!help** to get started with Villager Bot!\n\n" +
                                "Want to recieve updates, report a bug, or make suggestions? Join the official [support server](https://discord.gg/39DwwUV)!")
        while i >= 0:
            try:
                await guild.channels[i].send(embed=join_msg)
            except Exception:
                i += 1
                pass
            else:
                i = -100

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.db.drop_do_replies(guild.id)
        await self.db.drop_prefix(guild.id)


def setup(bot):
    bot.add_cog(Events(bot))
