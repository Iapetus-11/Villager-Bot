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

        if "@Villager Bot#6423" in message.content:
            prefix = await self.db.get_prefix(message.guild.id)
            help_embed = discord.Embed(color=discord.Color.green())
            help_embed.set_author(
                name="Villager Bot Commands",
                icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
            help_embed.add_field(name="Minecraft", value=f"``{prefix}help mc``", inline=True)
            help_embed.add_field(name="Fun", value=f"``{prefix}help fun``", inline=True)
            help_embed.add_field(name="\uFEFF", value=f"\uFEFF", inline=True)
            help_embed.add_field(name="Useful", value=f"``{prefix}help useful``", inline=True)
            help_embed.add_field(name="Admin", value=f"``{prefix}help admin``", inline=True)
            help_embed.add_field(name="\uFEFF", value=f"\uFEFF", inline=True)
            help_embed.add_field(name="\uFEFF", value="""Need more help? Check out the Villager Bot [Support Server](https://discord.gg/39DwwUV)
            Enjoying the bot? Vote for us on [top.gg](https://top.gg/bot/639498607632056321/vote)""", inline=False)
            help_embed.set_footer(text=choice(self.bot.get_cog("Useful").tips)
            await ctx.send(embed=help_embed)

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
