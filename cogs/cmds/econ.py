from discord.ext import commands
import discord
import asyncio
import math


class Econ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog("Database")

    @commands.command(name='bal', aliases=['balance'])
    async def bal(self, ctx, user: discord.User = None):
        """Shows the balance of a user or the message sender"""

        if u is None:
            u = ctx.author

        db_user = await self.db.fetch_user(user.id)

        u_items = await self.db.fetch_items(user.id)
        total_wealth = db_user['emeralds'] + db_user['vault_bal'] * 9 + sum([u_it['sell_price'] + u_it['item_amount'] for u_it in u_items])

        embed = discord.Embed(color=self.bot.cc)
        embed.set_author(name=f'{u.display_name}\'s emeralds', icon_url=u.avatar_url_as())

        embed.description = f'Total Wealth: {total_wealth}{self.bot.custom_emojis["emerald"]}'

        embed.add_field(name='Pocket', value=f'{db_user["emeralds"]}{self.bot.custom_emojis["emerald"]}')
        embed.add_field(name='Vault', value=f'{db_user["vault_bal"]}{self.bot.custom_emojis["emerald_block"]}/{db_user["vault_max"]}')

        await ctx.send(embed=embed)

    @commands.command(name='inv', aliases=['inventory', 'pocket'])
    async def inventory(self, ctx, user: discord.User = None):
        """Shows the inventory of a user or the message sender"""

        u_items = await self.db.fetch_items(user.id)
        items_sorted = sorted(u_items, key=lambda item: item['sell_price'], reverse=True)  # sort items by sell price
        items_chunks = [items_sorted[i:i + 16] for i in range(0, len(items_sorted), 16)]  # split items into chunks of 16 [[16..], [16..], [16..]]

        page = 0
        page_max = len(items_chunks)

        while True:
            body = ''  # text for that page
            for item in items_chunks[page]:
                it_am_txt = f'{item["item_amount"]}'
                it_am_txt += ' \uFEFF' * (len(it_am_txt - 5))
                body += f'`{it_am_txt}x` **{item["item_name"]}** ({item["sell_price"]}{self.bot.custom_emojis["emerald"]})\n'

            embed = discord.Embed(color=self.bot.cc, description=body)
            embed.set_author(name=f'{user.display_name}\'s inventory', icon_url=user.avatar_url_as())
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
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id and react.emoji in rs_used

                react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reaction from message author (3min)
            except asyncio.TimeoutError:
                return

            if react.emoji == '⬅️': page -= 1
            if react.emoji == '➡️': page += 1

    @commands.command(name='deposit', aliases=['dep'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def vault_deposit(self, ctx, emerald_blocks: str):
        """Deposits the given amount of emerald blocks into the vault"""

        db_user = await self.db.fetch_user(ctx.author.id)

        c_v_bal = db_user['vault_bal']
        c_v_max = db_user['vault_max']
        c_bal = db_user['emeralds']

        if c_bal < 9:
            await self.bot.send(ctx, 'You don\'t have enough emeralds to deposit.')
            return

        if amount.lower() in ('all', 'max',):
            amount = c_v_max - c_v_bal

            if amount * 9 > c_bal:
                amount = math.floor(c_bal / 9)
        else:
            try:
                amount = int(emerald_blocks)
            except ValueError:
                await self.bot.send(ctx, 'You have to use a number.')
                return

        if amount < 1:
            await self.bot.send(ctx, 'You can\'t deposit less than one emerald block.')
            return

        if amount > c_v_max - c_v_bal:
            await self.bot.send(ctx, 'You don\'t have enough space for that.')
            return

        await self.db.balance_sub(ctx.author.id, amount * 9)
        await self.db.set_vault(ctx.author.id, c_v_bal + amount, c_v_max)

        await self.bot.send(ctx, f'Deposited {amount}{self.bot.custom_emojis["emerald_block"]}'
        f'({amount * 9}{self.bot.custom_emojis["emerald"]}) into your vault.')

    @commands.command(name='withdraw', aliases=['with'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def vault_withdraw(self, ctx, emerald_blocks: str):
        """Withdraws a certain amount of emerald blocks from the vault"""

        db_user = await self.db.fetch_user(ctx.author.id)

        c_v_bal = db_user['vault_bal']
        c_v_max = db_user['vault_max']

        c_bal = db_user['emeralds']

        if c_v_bal < 1:
            await self.bot.send(ctx, 'You don\'t have enough emerald blocks to withdraw.')
            return

        if amount.lower() in ('all', 'max',):
            amount = c_v_bal
        else:
            try:
                amount = int(emerald_blocks)
            except ValueError:
                await self.bot.send(ctx, 'You have to use a number.')
                return

        if amount < 1:
            await self.bot.send(ctx, 'You can\'t withdraw less than one emerald block.')
            return

        if amount > c_v_bal:
            await self.bot.send(ctx, 'You can\'t withdraw more than you have.')
            return

        await self.db.balance_add(ctx.author.id, amount * 9)
        await self.db.set_vault(ctx.author.id, c_v_bal - amount, c_v_max)

        await self.bot.send(ctx, f'Withdrew {amount}{self.bot.custom_emojis["emerald_block"]}'
        f'({amount * 9}{self.bot.custom_emojis["emerald"]}) from your vault.')

    @commands.group(name='shop')
    async def shop(self, ctx):
        """Shows the available options in the Villager Shop"""

        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=self.bot.cc)
            embed.set_author(name='Villager Shop', icon_url=self.bot.splash_logo)

            embed.add_field(name='__**Tools**__', value=f'`{ctx.prefix}shop tools`')
            embed.add_field(name='__**Magic**__', value=f'`{ctx.prefix}shop magic`')
            embed.add_field(name='__**Other**__', value=f'`{ctx.prefix}shop other`')

            embed.set_footer(text=f'Use {ctx.prefix}inventory to see what you have!')

            await ctx.send(embed=embed)

    @shop.command(name='tools')
    async def shop_tools(self, ctx):
        """Allows you to shop for tools"""

        tool_items = []

        for item in [self.bot.shop_items[key] for key in list(self.bot.shop_items)]:  # filter out non-tool items
            if item[0] == 'tools':
                tool_items.append(item)

        tool_items_sorted = sorted(tool_items, key=lambda item: item[1])  # sort by buy price
        tool_items_chunked = [tool_items_sorted[i:i + 3] for i in range(0, len(tool_items_sorted), 3)]  # split items into chunks of 3

        page = 0
        page_max = len(tool_items_chunked)

        msg = None

        while True:
            embed = discord.Embed(color=self.bot.cc)
            embed.set_author(name='Villager Shop [Tools]', icon_url=self.bot.splash_logo)

            for item in tool_items_chunked[page]:
                embed.add_field(name=item[3][0], value=f'`{ctx.prefix}buy {item[3][0].lower()}`')

            embed.set_footer(text=f'Page {page+1}/{page_max}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            await msg.add_reaction('⬅️')
            await msg.add_reaction('➡️')

            try:
                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reaction from message author (3min)
            except asyncio.TimeoutError:
                return

            await react.remove(ctx.author)

            if react.emoji == '⬅️': page -= 1
            if react.emoji == '➡️': page += 1

            if page > page_max - 1: page = page_max - 1
            if page < 0: page = 0

    @shop.command(name='magic')
    async def shop_magic(self, ctx):
        """Allows you to shop for magic items"""

        magic_items = []

        for item in [self.bot.shop_items[key] for key in list(self.bot.shop_items)]:  # filter out non-tool items
            if item[0] == 'magic':
                magic_items.append(item)

        magic_items_sorted = sorted(magic_items, key=lambda item: item[1])  # sort by buy price
        magic_items_chunked = [magic_items_sorted[i:i + 3] for i in range(0, len(magic_items_sorted), 3)]  # split items into chunks of 3

        page = 0
        page_max = len(magic_items_chunked)

        msg = None

        while True:
            embed = discord.Embed(color=self.bot.cc)
            embed.set_author(name='Villager Shop [Magic]', icon_url=self.bot.splash_logo)

            for item in magic_items_chunked[page]:
                embed.add_field(name=item[3][0], value=f'`{ctx.prefix}buy {item[3][0].lower()}`')

            embed.set_footer(text=f'Page {page+1}/{page_max}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            await msg.add_reaction('⬅️')
            await msg.add_reaction('➡️')

            try:
                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reaction from message author (3min)
            except asyncio.TimeoutError:
                return

            await react.remove(ctx.author)

            if react.emoji == '⬅️': page -= 1
            if react.emoji == '➡️': page += 1

            if page > page_max - 1: page = page_max - 1
            if page < 0: page = 0

    @shop.command(name='other')
    async def shop_other(self, ctx):
        """Allows you to shop for other/miscellaneous items"""

        other_items = []

        for item in [self.bot.shop_items[key] for key in list(self.bot.shop_items)]:  # filter out non-tool items
            if item[0] == 'other':
                other_items.append(item)

        other_items_sorted = sorted(other_items, key=lambda item: item[1])  # sort by buy price
        other_items_chunked = [other_items_sorted[i:i + 3] for i in range(0, len(other_items_sorted), 3)]  # split items into chunks of 3

        page = 0
        page_max = len(other_items_chunked)

        msg = None

        while True:
            embed = discord.Embed(color=self.bot.cc)
            embed.set_author(name='Villager Shop [Other]', icon_url=self.bot.splash_logo)

            for item in other_items_chunked[page]:
                embed.add_field(name=item[3][0], value=f'`{ctx.prefix}buy {item[3][0].lower()}`')

            embed.set_footer(text=f'Page {page+1}/{page_max}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            await msg.add_reaction('⬅️')
            await msg.add_reaction('➡️')

            try:
                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reaction from message author (3min)
            except asyncio.TimeoutError:
                return

            await react.remove(ctx.author)

            if react.emoji == '⬅️': page -= 1
            if react.emoji == '➡️': page += 1

            if page > page_max - 1: page = page_max - 1
            if page < 0: page = 0


def setup(bot):
    bot.add_cog(Econ(bot))
