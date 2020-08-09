from discord.ext import commands
import discord
import asyncio


class Econ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog("Database")

    @commands.command(name='bal', aliases=['balance'])
    async def bal(self, ctx, u: discord.User = None):
        """Shows the balance of a user or the message sender"""

        if u is None:
            u = ctx.author

        db_user = await self.db.fetch_user(u.id)

        embed = discord.Embed(color=self.bot.cc)
        embed.set_author(name=f'{u.display_name}\'s emeralds', icon_url=u.avatar_url_as())

        embed.add_field(name='Pocket', value=f'{db_user["emeralds"]}{self.bot.custom_emojis["emerald"]}')
        embed.add_field(name='Vault', value=f'{db_user["vault_bal"]}{self.bot.custom_emojis["emerald_block"]}/{db_user["vault_max"]}')

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Econ(bot))
