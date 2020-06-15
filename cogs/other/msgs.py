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

        if message.clean_content.startswith("@" + message.guild.get_member(self.bot.user.id).display_name):
            if message.guild is not None:
                prefix = await self.db.get_prefix(message.guild.id)
                prefix = prefix if prefix is not None else "!!"
            else:
                prefix = "!!"
            help_embed = discord.Embed(color=discord.Color.green(), description=f"The prefix for this server is ``{prefix}`` and the help command is ``{prefix}help``\n"
                                                                                "If you are in need of more help, you can join the **[Support Server](https://discord.gg/39DwwUV)**.")
            help_embed.set_author(
                name="Villager Bot",
                icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
            help_embed.set_footer(text="Made by Iapetus11 & TrustedMercury!")
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
