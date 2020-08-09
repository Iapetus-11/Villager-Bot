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

        u_items = await self.db.fetch_items(u.id)
        total_wealth = db_user['emeralds'] + db_user['vault_bal'] * 9 + sum([u_it['sell_price'] + u_it['item_amount'] for u_it in u_items])

        embed = discord.Embed(color=self.bot.cc)
        embed.set_author(name=f'{u.display_name}\'s emeralds', icon_url=u.avatar_url_as())

        embed.description = f'Total Wealth: {total_wealth}{self.bot.custom_emojis["emerald"]}'

        embed.add_field(name='Pocket', value=f'{db_user["emeralds"]}{self.bot.custom_emojis["emerald"]}')
        embed.add_field(name='Vault', value=f'{db_user["vault_bal"]}{self.bot.custom_emojis["emerald_block"]}/{db_user["vault_max"]}')

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Econ(bot))
