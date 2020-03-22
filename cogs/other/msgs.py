from discord.ext import commands
import discord
from random import choice


class Msgs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog("Database")
        self.g = self.bot.get_cog("Global")

    @commands.Cog.listener()
    async def on_message(self, message):
        self.g.msg_count += 1
        await self.db.incrementVaultMax(message.author.id)

        # Only replies handling past this point
        if message.author.bot:
            return

        if "emerald" in message.clean_content.lower() or "villager bot" in message.clean_content.lower():
            if message.guild is None or await self.db.getDoReplies(message.guild.id):
                try:
                    await message.channel.send(choice(["hrmm", "hmm", "hrmmm", "hrghhmmm", "hrhhmmmmmmmmm", "hrmmmmmm", "hrmmmmmmmmmm", "hrmmmmm"]))
                except discord.errors.Forbidden:
                    pass


def setup(bot):
    bot.add_cog(Msgs(bot))
