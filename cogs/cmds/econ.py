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

    @commands.command(name='inv', aliases=['inventory', 'pocket'])
    async def inventory(self, ctx, u: discord.User = None):
        """Shows the inventory of a user or the message sender"""

        u_items = await self.db.fetch_items(u.id)
        items_sorted = sorted(u_items, key=lambda item: item['sell_price'])  # sort items by sell price
        items_chunks = [items_sorted[i:i + 16] for i in range(0, len(items_sorted), 16)]  # split items into chunks of 16 [[16..], [16..], [16..]]

        page = 0
        page_max = len(items_chunks)

        while True:
            body = ''
            for item in items_chunks[page]:
                it_am_txt = f'{item["item_amount"]}'
                it_am_txt += ' \uFEFF' * (len(it_am_txt - 5))
                body += f'`{it_am_txt}x` **{item["item_name"]}** ({item["sell_price"]}{self.bot.custom_emojis["emerald"]})\n'

            embed = discord.Embed(color=self.bot.cc, description=body)
            embed.set_author(name=f'{u.display_name}\'s inventory', icon_url=u.avatar_url_as())
            embed.set_footer(text=f'Page {page+1}/{page_max+1}')

            msg = await ctx.send(embed=embed)

            rs_used = []

            if page != page_max:
                rs_used.append('➡️')
                await msg.add_reaction('➡️')

            if page != 0:
                rs_used.append('⬅️')
                await msg.add_reaction('⬅️')

            try:
                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and react.emoji in rs_used

                react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reacton from message author
            except asyncio.TimeoutError:
                return

            if react.emoji == '⬅️': page -= 1
            if react.emoji == '➡️': page += 1


def setup(bot):
    bot.add_cog(Econ(bot))
