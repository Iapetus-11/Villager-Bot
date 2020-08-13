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

        msg = None

        while True:
            body = ''  # text for that page
            for item in items_chunks[page]:
                it_am_txt = f'{item["item_amount"]}'
                it_am_txt += ' \uFEFF' * (len(it_am_txt - 5))
                body += f'`{it_am_txt}x` **{item["item_name"]}** ({item["sell_price"]}{self.bot.custom_emojis["emerald"]})\n'

            embed = discord.Embed(color=self.bot.cc, description=body)
            embed.set_author(name=f'{user.display_name}\'s inventory', icon_url=user.avatar_url_as())
            embed.set_footer(text=f'Page {page+1}/{page_max+1}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

            await msg.add_reaction('➡️')
            await asyncio.sleep(.1)
            await msg.add_reaction('⬅️')
            await asyncio.sleep(.1)

            try:
                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reaction from message author (3min)
            except asyncio.TimeoutError:
                return

            if react.emoji == '⬅️': page -= 1
            if react.emoji == '➡️': page += 1
            await asyncio.sleep(.1)

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

    async def format_required(self, item):
        if item[3][0] == 'Netherite Pickaxe':
            return f' ({item[1]}{self.bot.custom_emojis["emerald"]} + 6{self.bot.custom_emojis["netherite"]})'

        if item[3][0] == 'Netherite Sword':
            return f' ({item[1]}{self.bot.custom_emojis["emerald"]} + 6{self.bot.custom_emojis["netherite"]})'

        return f' ({item[1]}{self.bot.custom_emojis["emerald"]})'

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
                embed.add_field(name=f'{item[3][0]} {await self.format_required(item)}', value=f'`{ctx.prefix}buy {item[3][0].lower()}`', inline=False)

            embed.set_footer(text=f'Page {page+1}/{page_max}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            await asyncio.sleep(.1)
            await msg.add_reaction('⬅️')
            await asyncio.sleep(.1)
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
            await asyncio.sleep(.1)

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
                embed.add_field(name=f'{item[3][0]} {await self.format_required(item)}', value=f'`{ctx.prefix}buy {item[3][0].lower()}`', inline=False)

            embed.set_footer(text=f'Page {page+1}/{page_max}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            await asyncio.sleep(.1)
            await msg.add_reaction('⬅️')
            await asyncio.sleep(.1)
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
            await asyncio.sleep(.1)

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
                embed.add_field(name=f'{item[3][0]} {await self.format_required(item)}', value=f'`{ctx.prefix}buy {item[3][0].lower()}`', inline=False)

            embed.set_footer(text=f'Page {page+1}/{page_max}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            await asyncio.sleep(.1)
            await msg.add_reaction('⬅️')
            await asyncio.sleep(.1)
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
            await asyncio.sleep(.1)

    @commands.command(name='buy')
    async def buy(self, ctx, *, amount_item):
        amount_item = amount_item.lower()

        db_user = await self.db.fetch_user(ctx.author.id)

        if amount_item.startswith('max ') or item.startswith('all '):
            item = item[4:]
            amount = math.floor(db_user['emeralds'] / self.bot.shop_items[item])

            if amount < 1:
                await self.bot.send(ctx, 'You don\'t have enough emeralds to buy any of this item.')
                return
        else:
            split = amount_item.split(' ')

            try:
                amount = int(split.pop(0))
            except ValueError:
                amount = 1

            item = ' '.join(split)

        if amount < 1:
            await self.bot.send(ctx, 'You can\'t buy less than one of an item.')
            return

        shop_item = self.bot.shop_items.get(item)

        if shop_item is None:
            await self.bot.send(ctx, f'`{item}` is invalid or isn\'t in the Villager Shop.')
            return

        db_item = await self.db.fetch_item(ctx.author.id, shop_item[3][0])

        if shop_item[2] == "db_item_count < 1":
            amount = 1

        if shop_item[1] * amount < db_user['emeralds']:
            if db_item is not None:
                db_item_count = db_item['item_amount']
            else:
                db_item_count = 0

        if eval(shop_item[2]):
            if shop_item[3][0].startswith('Netherite'):
                db_scrap = await self.db.fetch_item(ctx.author.id, 'Netherite Scrap')

                if 'Sword' in shop_item[3][0]:
                    required = 6

                if 'Pickaxe' in shop_item[3][0]:
                    required = 3

                if scrap is not None and db_scrap['item_amount'] >= required:
                    await self.db.remove_item(ctx.author.id, 'Netherite Scrap', required)
                else:
                    await self.bot.send(ctx, f'You need a total of {required}{self.bot.cusom_emojis["netherite"]} (Netherite Scrap) to buy this item.')
                    return

            await self.db.balance_sub(ctx.author.id, shop_item[1] * amount)
            await self.db.add_item(ctx.author.id, shop_item[3][0], shop_item[3][1], amount)

            await self.bot.send(ctx, f'You have bought {amount}x **{shop_item[3][0]}**!'
            f'for {amount * shop_item[1]}{self.bot.custom_emojis["emerald"]} (You have {amount + db_item["item_amount"]} total)')

            if shop_item[3][0] == 'Rich Person Trophy':
                await self.db.rich_trophy_wipe(ctx.author.id)


def setup(bot):
    bot.add_cog(Econ(bot))
