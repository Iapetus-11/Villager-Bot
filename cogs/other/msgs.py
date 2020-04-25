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

        if "@Villager Bot" in message.clean_content:
            if message.guild is not None:
                prefix = await self.db.get_prefix(message.guild.id)
            else:
                prefix = "!!"
            help_embed = discord.Embed(color=discord.Color.green(),
                                       description=f"The prefix for this server is ``{prefix}``\nFor help, either join the [support server](https://discord.gg/39DwwUV) or use the ``{prefix}help`` command.")
            help_embed.set_author(
                name="Villager Bot",
                icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
            help_embed.set_footer(text=choice(self.bot.get_cog("Useful").tips))
            try:
                await message.channel.send(embed=help_embed)
            except discord.Forbidden:
                pass

        # Only replies handling past this point
        if message.author.bot:
            return

        if "emerald" in message.content.lower() or "villager bot" in message.clean_content.lower():
            if message.guild is None or await self.db.get_do_replies(message.guild.id):
                try:
                    await message.channel.send(choice(["hrmm", "hmm", "hrmmm", "hrghhmmm", "hrhhmmmmmmmmm", "hrmmmmmm", "hrmmmmmmmmmm", "hrmmmmm"]))
                except discord.errors.Forbidden:
                    pass
            return


def setup(bot):
    bot.add_cog(Msgs(bot))
