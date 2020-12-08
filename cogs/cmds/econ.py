from discord.ext import commands, tasks
from util.misc import make_health_bar
import discord
import asyncio
import aiohttp
import random
import arrow
import math


class Econ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

        if self.d.honey_buckets is not None:
            self.honey._buckets = self.d.honey_buckets

        self.pillage_cap_reset.start()

        # This links the max concurrency of the with, dep, sell, give, etc.. cmds
        for command in (self.vault_deposit, self.vault_withdraw, self.buy, self.sell, self.give, self.gamble, self.search, self.mine, self.pillage):
            command._max_concurrency = self.max_concurrency_dummy._max_concurrency

    def cog_unload(self):
        self.d.honey_buckets = self.honey._buckets

        self.pillage_cap_reset.cancel()

    @tasks.loop(hours=12)
    async def pillage_cap_reset(self):
        self.d.pillagers = {}
        self.d.pillages = {}

    @pillage_cap_reset.before_loop
    async def before_pillage_cap_reset(self):
        await self.bot.wait_until_ready()

    async def format_required(self, item, amount=1):
        if item[3][0] == 'Netherite Pickaxe':
            return f' {item[1] * amount}{self.d.emojis.emerald} + {4 * amount}{self.d.emojis.netherite}'

        if item[3][0] == 'Netherite Sword':
            return f' {item[1] * amount}{self.d.emojis.emerald} + {6 * amount}{self.d.emojis.netherite}'

        return f' {item[1] * amount}{self.d.emojis.emerald}'

    async def math_problem(self, ctx, source_multi=1):
        mine_commands = self.d.miners.get(ctx.author.id, 0)
        self.d.miners[ctx.author.id] = mine_commands + 1

        if mine_commands >= 100*source_multi:
            prob = f'{random.randint(0, 45)}{random.choice(("+", "+",))}{random.randint(0, 25)}'
            prob = (prob, str(eval(prob)),)

            await self.bot.send(ctx, ctx.l.econ.math_problem.problem.format(prob[0]))

            def author_check(m):
                return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

            try:
                m = await self.bot.wait_for('message', check=author_check, timeout=10)
            except asyncio.TimeoutError:
                await self.bot.send(ctx, ctx.l.econ.math_problem.timeout)
                return False

            if m.content != prob[1]:
                await self.bot.send(ctx, ctx.l.econ.math_problem.incorrect.format(self.d.emojis.no))
                return False

            self.d.miners[ctx.author.id] = 0
            await self.bot.send(ctx, ctx.l.econ.math_problem.correct.format(self.d.emojis.yes))

        return True

    @commands.command(name='max_concurrency_dummy')
    @commands.max_concurrency(1, commands.BucketType.user)
    async def max_concurrency_dummy(self, ctx):
        pass

    @commands.command(name='profile', aliases=['pp'])
    async def profile(self, ctx, *, user: discord.User = None):
        if user is None:
            user = ctx.author

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.send(ctx, ctx.l.econ.pp.bot_1)
            else:
                await self.bot.send(ctx, ctx.l.econ.pp.bot_2)
            return

        db_user = await self.db.fetch_user(user.id)
        u_items = await self.db.fetch_items(user.id)

        total_wealth = db_user['emeralds'] + db_user.get('vault_bal', 0) * 9 + sum([u_it.get('sell_price', 0) * u_it.get('amount', 0) for u_it in u_items])
        health_bar = make_health_bar(db_user['health'], 20, self.d.emojis.heart_full, self.d.emojis.heart_half, self.d.emojis.heart_empty)

        vote_streak = db_user['vote_streak']
        voted = arrow.utcnow().shift(hours=-12) < arrow.get(0 if db_user['streak_time'] is None else db_user['streak_time'])

        embed = discord.Embed(color=self.d.cc, description=health_bar)
        embed.set_author(name=user.display_name, icon_url=user.avatar_url_as())

        embed.add_field(name=ctx.l.econ.pp.total_wealth, value=f'{total_wealth}{self.d.emojis.emerald}')
        embed.add_field(name='\uFEFF', value='\uFEFF')
        embed.add_field(name=ctx.l.econ.pp.cmds_sent, value=self.d.cmd_lb.get(user.id, 0))

        embed.add_field(name=ctx.l.econ.pp.streak, value=(vote_streak if vote_streak else 0))
        embed.add_field(name='\uFEFF', value='\uFEFF')
        embed.add_field(name=ctx.l.econ.pp.can_vote, value=voted*ctx.l.econ.pp.nope+ctx.l.econ.pp.yep*(not voted))

        embed.add_field(name=ctx.l.econ.pp.pick, value=(await self.db.fetch_pickaxe(user.id)))
        embed.add_field(name='\uFEFF', value='\uFEFF')
        embed.add_field(name=ctx.l.econ.pp.sword, value=(await self.db.fetch_sword(user.id)))

        await ctx.send(embed=embed)

    @commands.command(name='balance', aliases=['bal', 'vault'])
    async def balance(self, ctx, *, user: discord.User = None):
        """Shows the balance of a user or the message sender"""

        if user is None:
            user = ctx.author

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.send(ctx, ctx.l.econ.bal.bot_1)
            else:
                await self.bot.send(ctx, ctx.l.econ.bal.bot_2)
            return

        db_user = await self.db.fetch_user(user.id)

        u_items = await self.db.fetch_items(user.id)

        vault_bal = db_user['vault_bal']

        total_wealth = db_user['emeralds'] + ((0 if vault_bal is None else vault_bal) * 9)
        total_wealth += sum([u_it['sell_price'] * u_it.get('amount', 0) for u_it in u_items])

        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name=ctx.l.econ.bal.s_emeralds.format(user.display_name), icon_url=user.avatar_url_as())

        embed.description = ctx.l.econ.bal.total_wealth.format(total_wealth, self.d.emojis.emerald)

        embed.add_field(name=ctx.l.econ.bal.pocket, value=f'{db_user["emeralds"]}{self.d.emojis.emerald}')
        embed.add_field(name=ctx.l.econ.bal.vault, value=f'{db_user["vault_bal"]}{self.d.emojis.emerald_block}/{db_user["vault_max"]}')

        await ctx.send(embed=embed)

    @commands.command(name='inv', aliases=['inventory', 'pocket'])
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def inventory(self, ctx, *, user: discord.User = None):
        """Shows the inventory of a user or the message sender"""

        if user is None:
            user = ctx.author

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.send(ctx, ctx.l.econ.inv.bot_1)
            else:
                await self.bot.send(ctx, ctx.l.econ.inv.bot_2)
            return

        u_items = await self.db.fetch_items(user.id)
        items_sorted = sorted(u_items, key=lambda item: item['sell_price'], reverse=True)  # sort items by sell price
        items_chunks = [items_sorted[i:i + 16] for i in range(0, len(items_sorted), 16)]  # split items into chunks of 16 [[16..], [16..], [16..]]

        page = 0
        page_max = len(items_chunks)-1

        if items_chunks == []:
            items_chunks = [[]]
            page_max = 0

        msg = None
        first_time = True

        while True:
            body = ''  # text for that page
            for item in items_chunks[page]:
                it_am_txt = f'{item["amount"]}'
                #it_am_txt += ' \uFEFF' * (len(it_am_txt) - 5)
                body += f'`{it_am_txt}x` **{item["name"]}** ({item["sell_price"]}{self.d.emojis.emerald})\n'

            embed = discord.Embed(color=self.d.cc, description=body)
            embed.set_author(name=ctx.l.econ.inv.s_inventory.format(user.display_name), icon_url=user.avatar_url_as())
            embed.set_footer(text=f'{ctx.l.econ.page} {page+1}/{page_max+1}')

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

            if page_max > 0:
                if first_time:
                    await msg.add_reaction('⬅️')
                    await asyncio.sleep(.1)
                    await msg.add_reaction('➡️')
                    await asyncio.sleep(.1)
                try:
                    def author_check(react, r_user):
                        return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                    react, r_user = await self.bot.wait_for('reaction_add', check=author_check, timeout=180)  # wait for reaction from message author (3min)
                except asyncio.TimeoutError:
                    return

                await react.remove(ctx.author)

                if react.emoji == '⬅️': page -= 1 if page-1 >= 0 else 0
                if react.emoji == '➡️': page += 1 if page+1 <= page_max else 0
                await asyncio.sleep(.1)
            else:
                break

            first_time = False

    @commands.command(name='deposit', aliases=['dep'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def vault_deposit(self, ctx, emerald_blocks: str):
        """Deposits the given amount of emerald blocks into the vault"""

        db_user = await self.db.fetch_user(ctx.author.id)

        c_v_bal = db_user['vault_bal']
        c_v_max = db_user['vault_max']
        c_bal = db_user['emeralds']

        if c_bal < 9:
            await self.bot.send(ctx, ctx.l.econ.dep.poor_loser)
            return

        if emerald_blocks.lower() in ('all', 'max',):
            amount = c_v_max - c_v_bal

            if amount * 9 > c_bal:
                amount = math.floor(c_bal / 9)
        else:
            try:
                amount = int(emerald_blocks)
            except ValueError:
                await self.bot.send(ctx, ctx.l.econ.use_a_number_stupid)
                return

        if amount * 9 > c_bal:
            await self.bot.send(ctx, ctx.l.econ.dep.stupid_3)
            return

        if amount < 1:
            if emerald_blocks.lower() in ('all', 'max',):
                await self.bot.send(ctx, ctx.l.econ.dep.stupid_2)
            else:
                await self.bot.send(ctx, ctx.l.econ.dep.stupid_1)

            return

        if amount > c_v_max - c_v_bal:
            await self.bot.send(ctx, ctx.l.econ.dep.stupid_2)
            return

        await self.db.balance_sub(ctx.author.id, amount * 9)
        await self.db.set_vault(ctx.author.id, c_v_bal + amount, c_v_max)

        await self.bot.send(ctx, ctx.l.econ.dep.deposited.format(amount, self.d.emojis.emerald_block, amount*9, self.d.emojis.emerald))

    @commands.command(name='withdraw', aliases=['with'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def vault_withdraw(self, ctx, emerald_blocks: str):
        """Withdraws a certain amount of emerald blocks from the vault"""

        db_user = await self.db.fetch_user(ctx.author.id)

        c_v_bal = db_user['vault_bal']
        c_v_max = db_user['vault_max']

        c_bal = db_user['emeralds']

        if c_v_bal < 1:
            await self.bot.send(ctx, ctx.l.econ.withd.poor_loser)
            return

        if emerald_blocks.lower() in ('all', 'max',):
            amount = c_v_bal
        else:
            try:
                amount = int(emerald_blocks)
            except ValueError:
                await self.bot.send(ctx, ctx.l.econ.use_a_number_stupid)
                return

        if amount < 1:
            await self.bot.send(ctx, ctx.l.econ.withd.stupid_1)
            return

        if amount > c_v_bal:
            await self.bot.send(ctx, ctx.l.econ.withd.stupid_2)
            return

        await self.db.balance_add(ctx.author.id, amount * 9)
        await self.db.set_vault(ctx.author.id, c_v_bal - amount, c_v_max)

        await self.bot.send(ctx, ctx.l.econ.withd.withdrew.format(amount, self.d.emojis.emerald_block, amount*9, self.d.emojis.emerald))

    @commands.group(name='shop')
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def shop(self, ctx):
        """Shows the available options in the Villager Shop"""

        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=ctx.l.econ.shop.villager_shop, icon_url=self.d.splash_logo)

            embed.add_field(name=f'__**{ctx.l.econ.shop.tools}**__', value=f'`{ctx.prefix}shop tools`')
            embed.add_field(name=f'__**{ctx.l.econ.shop.magic}**__', value=f'`{ctx.prefix}shop magic`')
            embed.add_field(name=f'__**{ctx.l.econ.shop.other}**__', value=f'`{ctx.prefix}shop other`')

            embed.set_footer(text=ctx.l.econ.shop.embed_footer.format(ctx.prefix))

            await ctx.send(embed=embed)

    async def shop_logic(self, ctx, _type, header):
        items = []

        for item in [self.d.shop_items[key] for key in list(self.d.shop_items)]:  # filter out items which aren't of the right _type
            if item[0] == _type:
                items.append(item)

        items_sorted = sorted(items, key=(lambda item: item[1]))  # sort by buy price
        items_chunked = [items_sorted[i:i + 4] for i in range(0, len(items_sorted), 4)]  # split into chunks of 4

        page = 0
        page_max = len(items_chunked)

        msg = None

        while True:
            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=header, icon_url=self.d.splash_logo)

            for item in items_chunked[page]:
                embed.add_field(name=f'{item[3][0]} ({await self.format_required(item)})', value=f'`{ctx.prefix}buy {item[3][0].lower()}`', inline=False)

            embed.set_footer(text=f'{ctx.l.econ.page} {page+1}/{page_max}')

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

    @shop.command(name='tools')
    async def shop_tools(self, ctx):
        """Allows you to shop for tools"""

        await self.shop_logic(ctx, 'tools', f'{ctx.l.econ.shop.villager_shop} [{ctx.l.econ.shop.tools}]')

    @shop.command(name='magic')
    async def shop_magic(self, ctx):
        """Allows you to shop for magic items"""

        await self.shop_logic(ctx, 'magic', f'{ctx.l.econ.shop.villager_shop} [{ctx.l.econ.shop.magic}]')

    @shop.command(name='other')
    async def shop_other(self, ctx):
        """Allows you to shop for other/miscellaneous items"""

        await self.shop_logic(ctx, 'other', f'{ctx.l.econ.shop.villager_shop} [{ctx.l.econ.shop.other}]')

    @commands.command(name='buy')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def buy(self, ctx, *, amount_item):
        """Allows you to buy items"""

        amount_item = amount_item.lower()

        db_user = await self.db.fetch_user(ctx.author.id)

        if amount_item.startswith('max ') or amount_item.startswith('all '):
            item = amount_item[4:]

            try:
                amount = math.floor(db_user['emeralds'] / self.d.shop_items[item][1])
            except KeyError:
                await self.bot.send(ctx, ctx.l.econ.buy.stupid_2.format(item))
                return

            if amount < 1:
                await self.bot.send(ctx, ctx.l.econ.buy.poor_loser_1)
                return
        else:
            split = amount_item.split(' ')

            try:
                amount = split.pop(0)
                amount = int(amount)
            except ValueError:
                item = amount
                item += (' ' + ' '.join(split)) if len(split) > 0 else ''
                amount = 1
            else:
                item = ' '.join(split)

        if amount < 1:
            await self.bot.send(ctx, ctx.l.econ.buy.stupid_1)
            return

        shop_item = self.d.shop_items.get(item)

        if shop_item is None:
            await self.bot.send(ctx, ctx.l.econ.buy.stupid_2.format(item))
            return

        db_item = await self.db.fetch_item(ctx.author.id, shop_item[3][0])

        if shop_item[2] == "db_item_count < 1":
            amount = 1

        if shop_item[1] * amount > db_user['emeralds']:
            await self.bot.send(ctx, ctx.l.econ.buy.poor_loser_2.format(amount, shop_item[3][0]))
            return

        if db_item is not None:
            db_item_count = db_item['amount']
        else:
            db_item_count = 0

        if eval(shop_item[2]):
            if shop_item[3][0] in ('Netherite Sword', 'Netherite Pickaxe',):
                db_scrap = await self.db.fetch_item(ctx.author.id, 'Netherite Scrap')

                if 'Sword' in shop_item[3][0]:
                    required = 6

                if 'Pickaxe' in shop_item[3][0]:
                    required = 4

                if db_scrap is not None and db_scrap['amount'] >= required:
                    await self.db.remove_item(ctx.author.id, 'Netherite Scrap', required)
                else:
                    await self.bot.send(ctx, ctx.l.econ.buy.need_total_of.format(required, self.d.emojis.netherite))
                    return

            await self.db.balance_sub(ctx.author.id, shop_item[1] * amount)
            await self.db.add_item(ctx.author.id, shop_item[3][0], shop_item[3][1], amount, shop_item[3][2])

            await self.bot.send(ctx,  # pep8 wants to kil me
                ctx.l.econ.buy.you_done_bought.format(
                    amount,
                    shop_item[3][0],
                    await self.format_required(shop_item, amount),
                    amount+db_item_count
                )
            )

            if shop_item[3][0] == 'Rich Person Trophy':
                await self.db.rich_trophy_wipe(ctx.author.id)

        else:
            if shop_item[2].startswith('db_item_count <'):
                await self.bot.send(ctx, ctx.l.econ.buy.no_to_item_1)
            else:
                await self.bot.send(ctx, ctx.l.econ.buy.no_to_item_2)

    @commands.command(name='sell')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def sell(self, ctx, *, amount_item):
        """Allows you to sell items"""

        amount_item = amount_item.lower()

        db_user = await self.db.fetch_user(ctx.author.id)

        if amount_item.startswith('max ') or amount_item.startswith('all '):
            item = amount_item[4:]
            db_item = await self.db.fetch_item(ctx.author.id, item)

            if db_item is None:
                await self.bot.send(ctx, ctx.l.econ.sell.invalid_item)
                return

            amount = db_item['amount']
        else:
            split = amount_item.split(' ')

            try:
                amount = split.pop(0)
                amount = int(amount)
            except ValueError:
                item = amount
                item += (' ' + ' '.join(split)) if len(split) > 0 else ''
                amount = 1
            else:
                item = ' '.join(split)

            db_item = await self.db.fetch_item(ctx.author.id, item)

        if db_item is None:
            await self.bot.send(ctx, ctx.l.econ.sell.invalid_item)
            return

        if amount > db_item['amount']:
            await self.bot.send(ctx, ctx.l.econ.sell.stupid_1)
            return

        if amount < 1:
            await self.bot.send(ctx, ctx.l.econ.sell.stupid_2)
            return

        await self.db.balance_add(ctx.author.id, amount * db_item['sell_price'])
        await self.db.remove_item(ctx.author.id, db_item['name'], amount)

        await self.bot.send(ctx, ctx.l.econ.sell.you_done_sold.format(amount, db_item['name'],
                                                                      amount*db_item['sell_price'],
                                                                      self.d.emojis.emerald))

    @commands.command(name='give', aliases=['gift', 'share'])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def give(self, ctx, user: discord.Member, *, amount_item):
        """Give an item or emeralds to another person"""

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.send(ctx, ctx.l.econ.give.bot_1)
            else:
                await self.bot.send(ctx, ctx.l.econ.give.bot_2)
            return

        if ctx.author.id == user.id:
            await self.bot.send(ctx, ctx.l.econ.give.stupid_1)
            return

        amount_item = amount_item.lower()
        try:
            # to be given is emeralds
            amount = int(amount_item)
            item = 'emerald'
        except Exception:
            split = amount_item.split(' ')
            try:
                temp_split = split.copy()
                amount = int(temp_split.pop(0))
                split = temp_split

            except Exception:
                amount = 1

            item = ' '.join(split)

        if amount < 1:
            await self.bot.send(ctx, ctx.l.econ.give.stupid_2)
            return

        db_user = await self.db.fetch_user(ctx.author.id)

        if 'pickaxe' in item.lower() or 'sword' in item.lower() or 'trophy' in item.lower() or 'amulet' in item.lower():
            await self.bot.send(ctx, ctx.l.econ.give.and_i_oop)
            return

        if item in ('emerald', 'emeralds', ':emerald:',):
            if amount > db_user["emeralds"]:
                await self.bot.send(ctx, ctx.l.econ.give.stupid_3)
                return

            await self.db.balance_sub(ctx.author.id, amount)
            await self.db.balance_add(user.id, amount)
            await self.db.log_transaction('emerald', amount, arrow.utcnow().timestamp, ctx.author.id, user.id)

            await self.bot.send(ctx, ctx.l.econ.give.gaveems.format(ctx.author.mention, amount, self.d.emojis.emerald, user.mention))

            if (await self.db.fetch_user(user.id))['give_alert']:
                await self.bot.send(user, ctx.l.econ.give.gaveyouems.format(ctx.author.mention, amount, self.d.emojis.emerald))
        else:
            db_item = await self.db.fetch_item(ctx.author.id, item)

            if db_item is None or amount > db_item['amount']:
                await self.bot.send(ctx, ctx.l.econ.give.stupid_4)
                return

            if db_item['sticky']:
                await self.bot.send(ctx, ctx.l.econ.give.and_i_oop)
                return

            if amount < 1:
                await self.bot.send(ctx, ctx.l.econ.give.stupid_2)
                return

            await self.db.remove_item(ctx.author.id, item, amount)
            await self.db.add_item(user.id, db_item['name'], db_item['sell_price'], amount)
            await self.db.log_transaction(db_item['name'], amount, arrow.utcnow().timestamp, ctx.author.id, user.id)

            await self.bot.send(ctx, ctx.l.econ.give.gave.format(ctx.author.mention, amount, db_item['name'], user.mention))

            if (await self.db.fetch_user(user.id))['give_alert']:
                await self.bot.send(user, ctx.l.econ.give.gaveyou.format(ctx.author.mention, amount, db_item['name']))

    @commands.command(name='gamble', aliases=['bet', 'stonk', 'stonks'])
    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def gamble(self, ctx, amount):
        """Gamble for emeralds with Villager Bot"""

        db_user = await self.db.fetch_user(ctx.author.id)

        if amount.lower() in ('all', 'max',):
            amount = db_user['emeralds']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await self.bot.send(ctx, ctx.l.econ.use_a_number_stupid)
                return

        if amount > db_user['emeralds']:
            await self.bot.send(ctx, ctx.l.econ.gamble.stupid_1)
            return

        if amount < 10:
            await self.bot.send(ctx, ctx.l.econ.gamble.stupid_2)
            return

        u_roll = random.randint(2, 12)
        b_roll = random.randint(2, 12)

        await self.bot.send(ctx, ctx.l.econ.gamble.roll.format(u_roll, b_roll))

        if u_roll > b_roll:
            multi = 100 + random.randint(5, 30) + (await self.db.fetch_item(ctx.author.id, 'Bane Of Pillagers Amulet') is not None) * 20
            multi += ((await self.db.fetch_item(ctx.author.id, 'Rich Person Trophy') is not None) * 20)
            multi = (150 + random.randint(-5, 0)) if multi >= 150 else multi
            multi /= 100

            if amount > 500:
                won = math.ceil(multi * math.ceil(math.log(amount, 1.009)))
            else:
                won = math.ceil(multi * amount)

            await self.db.balance_add(ctx.author.id, won)
            await self.bot.send(ctx, ctx.l.econ.gamble.win.format(random.choice(ctx.l.econ.gamble.actions), won, self.d.emojis.emerald))
        elif u_roll < b_roll:
            await self.db.balance_sub(ctx.author.id, amount)
            await self.bot.send(ctx, ctx.l.econ.gamble.lose.format(amount, self.d.emojis.emerald))
        else:
            await self.bot.send(ctx, ctx.l.econ.gamble.tie)

    @commands.command(name='search', aliases=['beg'])
    @commands.cooldown(1, 30*60, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def search(self, ctx):
        """Beg for emeralds"""

        db_user = await self.db.fetch_user(ctx.author.id)

        if random.choice([True, True, True, True, True, False]) or db_user['emeralds'] < 2:
            amount = 9 + math.ceil(math.log(db_user['emeralds']+1, 1.5)) + random.randint(1, 5)
            amount = random.randint(1, 4) if amount < 1 else amount

            await self.db.balance_add(ctx.author.id, amount)

            await self.bot.send(ctx, random.choice(ctx.l.econ.beg.positive).format(f'{amount}{self.d.emojis.emerald}'))
        else:
            amount = 9 + math.ceil(math.log(db_user['emeralds']+1, 1.3)) + random.randint(1, 5)  # ah yes, meth

            if amount < 1:
                amount = random.randint(1, 4)
            elif amount > 45000:
                amount = 45000 + random.randint(0, abs(int((amount - 45000))/3) + 1)

            if db_user['emeralds'] < amount:
                amount = db_user['emeralds']

            await self.db.balance_sub(ctx.author.id, amount)

            await self.bot.send(ctx, random.choice(ctx.l.econ.beg.negative).format(f'{amount}{self.d.emojis.emerald}'))

    @commands.command(name='mine', aliases=['mein', 'eun'])
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def mine(self, ctx):
        if not await self.math_problem(ctx): return

        db_user = await self.db.fetch_user(ctx.author.id)
        pickaxe = await self.db.fetch_pickaxe(ctx.author.id)

        # only works cause num of pickaxes is 6 and levels of fake finds is 3
        # please don't bug me about jank code, I know
        fake_finds = self.d.mining.finds[math.floor(self.d.mining.pickaxes.index(pickaxe)/2)]

        # calculate if user finds emeralds OR not
        yield_ = self.d.mining.yields_pickaxes[pickaxe] # [xTrue, xFalse]
        yield_chance_list = [True]*yield_[0] + [False]*yield_[1]
        found = random.choice(yield_chance_list)

        # ~~what the fuck?~~
        # calculate bonus emeralds from enchantment items
        for item in list(self.d.mining.yields_enchant_items):
            if await self.db.fetch_item(ctx.author.id, item) is not None:
                found += random.choice(self.d.mining.yields_enchant_items[item]) if found else 0
                break

        if not found:
            for item in self.d.findables:  # try to see if user gets an item
                if random.randint(0, item[2]) == 1:
                    await self.db.add_item(ctx.author.id, item[0], item[1], 1, item[3])

                    """
                    # god I hate multi language support fucking kill me
                    a = ''
                    if ctx.l.lang == 'en-us':
                        a = ' a'
                        if item[0][0] in self.d.vowels:  # angry noises
                            a = ' an'
                    """

                    await self.bot.send(ctx, ctx.l.econ.mine.found_item_1.format(
                        random.choice(ctx.l.econ.mine.actions),
                        1, item[0], item[1],  # shhhhh ignore the pep8 violations and move on
                        self.d.emojis.emerald,
                        random.choice(ctx.l.econ.mine.places)
                    ))

                    return

            await self.bot.send(ctx, ctx.l.econ.mine.found_item_2.format(
                random.choice(ctx.l.econ.mine.actions),
                random.randint(1, 6),
                random.choice(ctx.l.econ.mine.useless),
                random.choice(fake_finds)
            ))
        else:
            found = int(found)

            if await self.db.fetch_item(ctx.author.id, 'Rich Person Trophy') is not None:
                found *= 2  # sekret

            await self.db.balance_add(ctx.author.id, found)

            await self.bot.send(ctx, ctx.l.econ.mine.found_emeralds.format(random.choice(ctx.l.econ.mine.actions), found, self.d.emojis.emerald))

        if random.randint(0, 50) == 1:
            if db_user['vault_max'] < 2000:
                await self.db.update_user(ctx.author.id, 'vault_max', db_user['vault_max']+1)

    @commands.command(name='pillage', aliases=['bonk'])
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def pillage(self, ctx, victim: discord.User):
        if victim.bot:
            if victim.id == self.bot.user.id:
                await self.bot.send(ctx, ctx.l.econ.pillage.bot_1)
            else:
                await self.bot.send(ctx, ctx.l.econ.pillage.bot_2)
            return

        if ctx.author.id == victim.id:
            await self.bot.send(ctx, ctx.l.econ.pillage.stupid_1)
            return

        if ctx.guild.get_member(victim.id) is None:
            await self.bot.send(ctx, ctx.l.econ.pillage.stupid_2)
            return

        db_user = await self.db.fetch_user(ctx.author.id)

        if db_user['emeralds'] < 64:
            await self.bot.send(ctx, ctx.l.econ.pillage.stupid_3.format(self.d.emojis.emerald))
            return

        db_victim = await self.db.fetch_user(victim.id)

        if db_victim['emeralds'] < 64:
            await self.bot.send(ctx, ctx.l.econ.pillage.stupid_4.format(self.d.emojis.emerald))
            return

        pillager_pillages = self.d.pillagers.get(ctx.author.id, 0)
        self.d.pillagers[ctx.author.id] = pillager_pillages + 1

        times_pillaged = self.d.pillages.get(victim.id, 0)
        self.d.pillages[victim.id] = times_pillaged + 1

        user_bees = await self.db.fetch_item(ctx.author.id, 'Jar Of Bees')
        user_bees = 0 if user_bees is None else user_bees['amount']

        victim_bees = await self.db.fetch_item(victim.id, 'Jar Of Bees')
        victim_bees = 0 if victim_bees is None else victim_bees['amount']

        # lmao
        if pillager_pillages > 7 or times_pillaged > 4:
            chances = [False]*50 + [True]
        elif await self.db.fetch_item(victim.id, 'Bane Of Pillagers Amulet'):
            chances = [False]*5 + [True]
        elif user_bees > victim_bees:
            chances = [False]*3 + [True]*5
        elif user_bees < victim_bees:
            chances = [False]*5 + [True]*3
        else:
            chances = [True, False]

        pillager_sword_lvl =  self.d.sword_list.index((await self.db.fetch_sword(ctx.author.id)).lower())
        victim_sword_lvl = self.d.sword_list.index((await self.db.fetch_sword(victim.id)).lower())

        if pillager_sword_lvl > victim_sword_lvl:
            chances.append(True)
        elif pillager_sword_lvl < victim_sword_lvl:
            chances.append(False)

        success = random.choice(chances)

        if success:
            stolen = math.ceil(db_victim['emeralds'] * (random.randint(10, 40) / 100))
            adjusted = math.ceil(stolen * .92)  # villager bot will steal ur stuff

            await self.db.balance_sub(victim.id, stolen)
            await self.db.balance_add(ctx.author.id, adjusted)  # 8% tax

            await self.bot.send(ctx, random.choice(ctx.l.econ.pillage.u_win.user).format(adjusted, self.d.emojis.emerald))
            await self.bot.send(victim, random.choice(ctx.l.econ.pillage.u_win.victim).format(ctx.author.mention, stolen, self.d.emojis.emerald))

            await self.db.update_lb(ctx.author.id, 'pillages', adjusted, 'add')
        else:
            penalty = 32

            await self.db.balance_sub(ctx.author.id, penalty)
            await self.db.balance_add(victim.id, penalty)

            await self.bot.send(ctx, random.choice(ctx.l.econ.pillage.u_lose.user).format(penalty, self.d.emojis.emerald))
            await self.bot.send(victim, random.choice(ctx.l.econ.pillage.u_lose.victim).format(ctx.author.mention))

    @commands.command(name='use', aliases=['eat', 'chug'])
    @commands.cooldown(1, 0.25, commands.BucketType.user)
    async def use_item(self, ctx, *, _thing):
        """Allows you to use potions and some other items"""

        thing = _thing.lower()  # everyday bois

        current_pots = self.d.chuggers.get(ctx.author.id)

        if thing in ([] if current_pots is None else current_pots):
            await self.bot.send(ctx, ctx.l.econ.use.stupid_1)
            return

        db_item = await self.db.fetch_item(ctx.author.id, thing)

        if db_item is None:
            await self.bot.send(ctx, ctx.l.econ.use.stupid_2)
            return

        if thing == 'haste i potion':
            await self.db.remove_item(ctx.author.id, thing, 1)

            self.d.chuggers[ctx.author.id] = self.d.chuggers.get(ctx.author.id, [])  # ensure user has stuff there
            self.d.chuggers[ctx.author.id].append('Haste I Potion')

            await self.bot.send(ctx, ctx.l.econ.use.chug.format('Haste I Potion', 6))

            self.d.pause_econ.pop(ctx.author.id, None)

            await asyncio.sleep(60 * 6)

            await self.bot.send(ctx.author, ctx.l.econ.use.done.format('Haste I Potion'))

            self.d.chuggers[ctx.author.id].pop(self.d.chuggers[ctx.author.id].index('Haste I Potion'))  # pop pot from active potion fx
            return

        if thing == 'haste ii potion':
            await self.db.remove_item(ctx.author.id, thing, 1)

            self.d.chuggers[ctx.author.id] = self.d.chuggers.get(ctx.author.id, [])
            self.d.chuggers[ctx.author.id].append('Haste II Potion')

            await self.bot.send(ctx, ctx.l.econ.use.chug.format('Haste II Potion', 4.5))

            self.d.pause_econ.pop(ctx.author.id, None)

            await asyncio.sleep(60 * 4.5)

            await self.bot.send(ctx.author, ctx.l.econ.use.done.format('Haste II Potion'))

            self.d.chuggers[ctx.author.id].pop(self.d.chuggers[ctx.author.id].index('Haste II Potion'))  # pop pot from active potion fx
            return

        if thing == 'vault potion':
            db_user = await self.db.fetch_user(ctx.author.id)

            if db_user['vault_max'] > 1999:
                await self.bot.send(ctx, ctx.l.econ.use.vault_max)
                return

            add = random.randint(9, 15)

            if db_user['vault_max'] + add > 2000:
                add = 2000 - db_user['vault_max']

            await self.db.remove_item(ctx.author.id, 'Vault Potion', 1)
            await self.db.set_vault(ctx.author.id, db_user['vault_bal'], db_user['vault_max'] + add)

            await self.bot.send(ctx, ctx.l.econ.use.vault_pot.format(add))
            return

        if thing == 'honey jar':
            db_user = await self.db.fetch_user(ctx.author.id)

            if db_user['health'] < 20:
                await self.db.update_user(ctx.author.id, 'health', db_user['health']+1)

            await self.bot.send(ctx, ctx.l.econ.use.chug_no_end.format('Honey Jar'))
            return

        if thing == 'present':
            await self.db.remove_item(ctx.author.id, 'Present', 1)
            while True:
                for item in self.d.findables:
                    if random.randint(0, (item[2]//2)+2) == 1:
                        await self.db.add_item(ctx.author.id, item[0], item[1], 1, item[3])
                        await self.bot.send(ctx, random.choice(ctx.l.econ.use.present).format(item[0], item[1], self.d.emojis.emerald))
                        return

        await self.bot.send(ctx, ctx.l.econ.use.stupid_3)

    @commands.command(name='harvesthoney', aliases=['honey', 'horny'])  # ~~a strange urge occurs in me~~
    @commands.cooldown(1, 24*60*60, commands.BucketType.user)
    async def honey(self, ctx):
        bees = await self.db.fetch_item(ctx.author.id, 'Jar Of Bees')

        if bees is not None:
            bees = bees['amount']
        else:
            bees = 0

        if bees > 1024: bees = 1024

        if bees < 100:
            await self.bot.send(ctx, random.choice(ctx.l.econ.honey.stupid_1))
            ctx.command.reset_cooldown(ctx)
            return

        jars = bees - random.randint(math.ceil(bees / 6), math.ceil(bees / 2))
        await self.db.add_item(ctx.author.id, 'Honey Jar', 1, jars)

        await self.bot.send(ctx, random.choice(ctx.l.econ.honey.honey).format(jars))  # uwu so sticky oWo

        if random.choice([False]*3 + [True]):
            bees_lost = random.randint(math.ceil(bees / 75), math.ceil(bees / 50))

            await self.db.remove_item(ctx.author.id, 'Jar Of Bees', bees_lost)

            await self.bot.send(ctx, random.choice(ctx.l.econ.honey.ded).format(bees_lost))

    @commands.group(name='leaderboards', aliases=['lb', 'lbs', 'leaderboard'])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def leaderboards(self, ctx):
        if ctx.invoked_subcommand is None:
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.title)

            embed.add_field(name=ctx.l.econ.lb.emeralds, value=f'`{ctx.prefix}leaderboard emeralds`', inline=False)
            # Can't do tw due to the immense amount of resources required to calculate it for all users in the db (as is required)
            #embed.add_field(name='Total Wealth', value=f'`{ctx.prefix}leaderboard totalwealth`', inline=False)
            embed.add_field(name=ctx.l.econ.lb.stolen, value=f'`{ctx.prefix}leaderboard stolen`', inline=False)
            embed.add_field(name=ctx.l.econ.lb.kills, value=f'`{ctx.prefix}leaderboard mobkills`', inline=False)
            embed.add_field(name=ctx.l.econ.lb.bees, value=f'`{ctx.prefix}leaderboard bees`', inline=False)
            embed.add_field(name=ctx.l.econ.lb.cmds, value=f'`{ctx.prefix}leaderboard commands`', inline=False)
            embed.add_field(name=ctx.l.econ.lb.votes, value=f'`{ctx.prefix}leaderboard votes`', inline=False)

            await ctx.send(embed=embed)

    # assumes list is sorted prior
    # assumes list consists of tuple(uid, value)
    # rank_fstr is the template for each line
    async def leaderboard_logic(self, _list, origin_uid, rank_fstr):
        # find the rank/place on lb of the origin user
        u_place = -1
        for i in range(len(_list)):
            if _list[i][0] == origin_uid:
                u_place = i + 1
                origin_value = _list[i][1]
                break

        # shorten list
        _list = _list[:9] if u_place > 9 else _list[:10]

        body = ''

        for place, entry in enumerate(_list):  # enumerate() gives me a boner
            user = self.bot.get_user(entry[0])

            if user is None:
                user = 'Deleted User'
            else:
                user = discord.utils.escape_markdown(user.display_name)

            body += rank_fstr.format(place+1, entry[1], user)

        if u_place > 9:
            body += '\n⋮' + rank_fstr.format(u_place, origin_value, discord.utils.escape_markdown(self.bot.get_user(origin_uid).display_name))

        return body + '\uFEFF'

    @leaderboards.command(name='emeralds', aliases=['ems'])
    async def leaderboard_emeralds(self, ctx):
        emeralds = sorted((*await self.db.mass_fetch_balances()), key=(lambda tup: tup[1]), reverse=True)

        lb_global = await self.leaderboard_logic(emeralds, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.emerald))

        emeralds_local = [u for u in emeralds if ctx.guild.get_member(u[0])]
        lb_local = await self.leaderboard_logic(emeralds_local, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.emerald))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_ems.format(self.d.emojis.emerald_spinn))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.send(embed=embed)

    @leaderboards.command(name='pillages', aliases=['pil', 'stolen'])
    async def leaderboard_pillages(self, ctx):
        pillages = sorted((await self.db.mass_fetch_leaderboard('pillages')), key=(lambda tup: tup[1]), reverse=True)

        lb_global = await self.leaderboard_logic(pillages, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.emerald))

        pillages_local = [u for u in pillages if ctx.guild.get_member(u[0])]
        lb_local = await self.leaderboard_logic(pillages_local, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.emerald))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_pil.format(self.d.emojis.emerald))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.send(embed=embed)

    @leaderboards.command(name='mobkills', aliases=['kil', 'kills', 'kill', 'bonk'])
    async def leaderboard_mobkills(self, ctx):
        kills = sorted((await self.db.mass_fetch_leaderboard('mobs_killed')), key=(lambda tup: tup[1]), reverse=True)

        lb_global = await self.leaderboard_logic(kills, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.stevegun))

        kills_local = [u for u in kills if ctx.guild.get_member(u[0])]
        lb_local = await self.leaderboard_logic(kills_local, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.stevegun))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_kil.format(self.d.emojis.stevegun))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.send(embed=embed)

    @leaderboards.command(name='bees', aliases=['jarofbees', 'jarsofbees'])
    async def leaderboard_bees(self, ctx):
        bees = [(r['uid'], r['amount']) for r in await self.db.mass_fetch_item('Jar Of Bees')]
        bees = sorted(bees, key=(lambda tup: tup[1]), reverse=True)

        lb_global = await self.leaderboard_logic(bees, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.bee))

        bees_local = [u for u in bees if ctx.guild.get_member(u[0])]
        lb_local = await self.leaderboard_logic(bees_local, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.bee))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_bee.format(self.d.emojis.anibee))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.send(embed=embed)

    @leaderboards.command(name='commands', aliases=['cmds'])
    async def leaderboard_commands(self, ctx):
        cmds = sorted(self.d.cmd_lb.items(), key=(lambda tup: tup[1]), reverse=True)

        lb_global = await self.leaderboard_logic(cmds, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', ':keyboard:'))

        cmds_local = [u for u in cmds if ctx.guild.get_member(u[0])]
        lb_local = await self.leaderboard_logic(cmds_local, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', ':keyboard:'))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_cmds.format(':keyboard:'))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.send(embed=embed)

    @leaderboards.command(name='votes', aliases=['votestreaks', 'votestreak'])
    async def leaderboard_votes(self, ctx):
        vote_streaks = sorted(await self.db.mass_fetch_votestreaks(), key=(lambda tup: tup[1]), reverse=True)

        lb_global = await self.leaderboard_logic(vote_streaks, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.updoot))

        vote_streaks_local = [u for u in vote_streaks if ctx.guild.get_member(u[0])]
        lb_local = await self.leaderboard_logic(vote_streaks_local, ctx.author.id, '\n`{0}.` **{0}**{1} {0}'.format('{}', self.d.emojis.updoot))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_votes.format(':fire:'))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Econ(bot))
