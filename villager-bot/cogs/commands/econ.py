from collections import defaultdict
from discord.ext import commands
import functools
import discord
import asyncio
import random
import arrow
import math

from util.misc import lb_logic, format_required, make_health_bar, calc_total_wealth, emojify_item


class Econ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.db = bot.get_cog("Database")
        self.ipc = bot.ipc

        # This links the max concurrency of the with, dep, sell, give, etc.. cmds
        for command in (
            self.vault_deposit,
            self.vault_withdraw,
            self.buy,
            self.sell,
            self.give,
            self.gamble,
            self.search,
            self.mine,
            self.pillage,
        ):
            command._max_concurrency = self.max_concurrency_dummy._max_concurrency

        self._user_locks = defaultdict(asyncio.Lock)

    async def lock_author(self, ctx):
        await self._user_locks[ctx.author.id].acquire()

    async def unlock_author(self, ctx):
        self._user_locks[ctx.author.id].release()

    @functools.lru_cache(maxsize=None)  # calculate chances for a specific pickaxe to find emeralds
    def calc_yield_chance_list(self, pickaxe: str):
        yield_ = self.d.mining.yields_pickaxes[pickaxe]  # [xTrue, xFalse]
        return [True] * yield_[0] + [False] * yield_[1]

    async def math_problem(self, ctx, addition=1):
        # simultaneously updates the value in Karen and retrivies teh current value
        res = await self.ipc.request({"type": "mine-command", "user_id": ctx.author.id, "addition": addition})
        mine_commands = res.current

        if mine_commands >= 100:
            x, y = random.randint(0, 15), random.randint(0, 10)
            prob = f"{y*random.choice([chr(u) for u in (65279, 8203, 8204, 8205)])}{x}{x*random.choice([chr(u) for u in (65279, 8203, 8204, 8205)])}+{y}"
            prob = (prob, str(x + y))

            m = await ctx.reply(
                embed=discord.Embed(color=self.d.cc, description=ctx.l.econ.math_problem.problem.format("process.exit(69)")),
                mention_author=False,
            )
            asyncio.create_task(
                m.edit(embed=discord.Embed(color=self.d.cc, description=ctx.l.econ.math_problem.problem.format(prob[0])))
            )

            def author_check(m):
                return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

            try:
                m = await self.bot.wait_for("message", check=author_check, timeout=10)
            except asyncio.TimeoutError:
                await self.bot.reply_embed(ctx, ctx.l.econ.math_problem.timeout)
                return False

            if m.content != prob[1]:
                await self.bot.reply_embed(ctx, ctx.l.econ.math_problem.incorrect.format(self.d.emojis.no))
                return False

            await self.ipc.exec(f"mine_commands[{ctx.author.id}] = 0")
            await self.bot.reply_embed(ctx, ctx.l.econ.math_problem.correct.format(self.d.emojis.yes))

        return True

    @commands.command(name="max_concurrency_dummy")
    @commands.max_concurrency(1, commands.BucketType.user)
    async def max_concurrency_dummy(self, ctx):
        pass

    @commands.command(name="profile", aliases=["pp"])
    async def profile(self, ctx, *, user: discord.User = None):
        if user is None:
            user = ctx.author

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.reply_embed(ctx, ctx.l.econ.pp.bot_1)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.pp.bot_2)
            return

        db_user = await self.db.fetch_user(user.id)
        u_items = await self.db.fetch_items(user.id)

        total_wealth = calc_total_wealth(db_user, u_items)
        health_bar = make_health_bar(
            db_user["health"], 20, self.d.emojis.heart_full, self.d.emojis.heart_half, self.d.emojis.heart_empty
        )

        try:
            mooderalds = (await self.db.fetch_item(user.id, "Mooderald"))["amount"]
        except TypeError:
            mooderalds = 0

        vote_streak = db_user["vote_streak"]
        voted = arrow.utcnow().shift(hours=-12) < arrow.get(0 if db_user["last_vote"] is None else db_user["last_vote"])

        if arrow.utcnow().shift(days=-1, hours=-12) > arrow.get(0 if db_user["last_vote"] is None else db_user["last_vote"]):
            vote_streak = 0
            await self.db.update_user(user.id, vote_streak=0, last_vote=None)

        embed = discord.Embed(color=self.d.cc, description=health_bar)
        embed.set_author(name=user.display_name, icon_url=user.avatar_url_as())

        embed.add_field(name=ctx.l.econ.pp.total_wealth, value=f"{total_wealth}{self.d.emojis.emerald}")
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name=ctx.l.econ.pp.mooderalds, value=f"{mooderalds}{self.d.emojis.autistic_emerald}")

        embed.add_field(name=ctx.l.econ.pp.streak, value=(vote_streak if vote_streak else 0))
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name=ctx.l.econ.pp.can_vote, value=(ctx.l.econ.pp.nope if voted else ctx.l.econ.pp.yep))

        embed.add_field(name=ctx.l.econ.pp.pick, value=(await self.db.fetch_pickaxe(user.id)))
        embed.add_field(name="\uFEFF", value="\uFEFF")
        embed.add_field(name=ctx.l.econ.pp.sword, value=(await self.db.fetch_sword(user.id)))

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="balance", aliases=["bal", "vault", "pocket"])
    async def balance(self, ctx, *, user: discord.User = None):
        """Shows the balance of a user or the message sender"""

        if user is None:
            user = ctx.author

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.reply_embed(ctx, ctx.l.econ.bal.bot_1)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.bal.bot_2)

            return

        db_user = await self.db.fetch_user(user.id)
        u_items = await self.db.fetch_items(user.id)

        total_wealth = calc_total_wealth(db_user, u_items)

        mooderalds = await self.db.fetch_item(user.id, "Mooderald")

        if mooderalds is None:
            mooderalds = 0
        else:
            mooderalds = mooderalds["amount"]

        embed = discord.Embed(color=self.d.cc)
        embed.set_author(name=ctx.l.econ.bal.s_emeralds.format(user.display_name), icon_url=user.avatar_url_as())

        embed.description = (
            ctx.l.econ.bal.total_wealth.format(total_wealth, self.d.emojis.emerald)
            + "\n"
            + ctx.l.econ.bal.autistic_emeralds.format(mooderalds, self.d.emojis.autistic_emerald)
        )

        embed.add_field(name=ctx.l.econ.bal.pocket, value=f'{db_user["emeralds"]}{self.d.emojis.emerald}')
        embed.add_field(
            name=ctx.l.econ.bal.vault, value=f'{db_user["vault_balance"]}{self.d.emojis.emerald_block}/{db_user["vault_max"]}'
        )

        await ctx.reply(embed=embed, mention_author=False)

    async def inventory_logic(self, ctx, user, items: list, cat: str, items_per_page: int = 8):
        fishies = {fish.name: fish.current for fish in self.d.fishing.fish.values()}

        for i, item in enumerate(items):
            try:
                items[i] = {**item, "sell_price": fishies[item["name"]]}
            except KeyError:
                pass

            await asyncio.sleep(0)

        items_sorted = sorted(items, key=lambda item: item["sell_price"], reverse=True)  # sort items by sell price
        items_chunks = [
            items_sorted[i : i + items_per_page] for i in range(0, len(items_sorted), items_per_page)
        ]  # split items into chunks of 16 [[16..], [16..], [16..]]

        page = 0
        page_max = len(items_chunks) - 1

        if items_chunks == []:
            items_chunks = [[]]
            page_max = 0

        msg = None
        first_time = True

        while True:
            if len(items_chunks) == 0:
                body = ctx.l.econ.inv.empty
            else:
                body = ""  # text for that page

                for item in items_chunks[page]:
                    sell_price_nice = f'({item["sell_price"]}{self.d.emojis.emerald})' if item["sell_price"] != -1 else ""

                    body += f'{emojify_item(self.d, item["name"])} `{item["amount"]}x` **{item["name"]}** {sell_price_nice}\n'

                embed = discord.Embed(color=self.d.cc, description=body)
                embed.set_author(name=ctx.l.econ.inv.s_inventory.format(user.display_name, cat), icon_url=user.avatar_url_as())
                embed.set_footer(text=f"{ctx.l.econ.page} {page+1}/{page_max+1}")

            if msg is None:
                msg = await ctx.reply(embed=embed, mention_author=False)
            else:
                await msg.edit(embed=embed)

            if page_max > 0:
                if first_time:
                    await msg.add_reaction("⬅️")
                    await asyncio.sleep(0.1)
                    await msg.add_reaction("➡️")
                    await asyncio.sleep(0.1)

                try:

                    def author_check(react, r_user):
                        return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                    react, r_user = await self.bot.wait_for(
                        "reaction_add", check=author_check, timeout=(2 * 60)
                    )  # wait for reaction from message author
                except asyncio.TimeoutError:
                    return

                await react.remove(ctx.author)

                if react.emoji == "⬅️":
                    page -= 1 if page - 1 >= 0 else 0
                if react.emoji == "➡️":
                    page += 1 if page + 1 <= page_max else 0

                await asyncio.sleep(0.1)
            else:
                break

            first_time = False

    async def inventory_boiler(self, ctx, user: discord.User = None):
        if ctx.invoked_subcommand is not None:
            return False, None

        if user is None:
            user = ctx.author

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.reply_embed(ctx, ctx.l.econ.inv.bot_1)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.inv.bot_2)

            return False, user

        return True, user

    @commands.group(name="inventory", aliases=["inv", "items"])
    @commands.cooldown(2, 2, commands.BucketType.user)
    async def inventory(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        split = ctx.message.content.split()

        if len(split) <= 1:
            user = ctx.author
        else:
            try:
                user = await commands.UserConverter().convert(ctx, " ".join(split[1:]))
            except BaseException:
                raise commands.BadArgument

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.reply_embed(ctx, ctx.l.econ.inv.bot_1)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.inv.bot_2)

            return

        items = await self.db.fetch_items(user.id)

        await self.inventory_logic(ctx, user, items, ctx.l.econ.inv.cats.all, 16)

    @inventory.group(name="tools", aliases=["tool", "pickaxes", "swords"])
    async def inventory_tools(self, ctx, user: discord.User = None):
        valid, user = await self.inventory_boiler(ctx, user)

        if not valid:
            return

        items = [e for e in await self.db.fetch_items(user.id) if e["name"] in self.d.cats.tools]

        await self.inventory_logic(ctx, user, items, ctx.l.econ.inv.cats.tools)

    @inventory.group(name="magic", aliases=["books", "potions", "enchants"])
    async def inventory_magic(self, ctx, user: discord.User = None):
        valid, user = await self.inventory_boiler(ctx, user)

        if not valid:
            return

        items = [e for e in await self.db.fetch_items(user.id) if e["name"] in self.d.cats.magic]

        await self.inventory_logic(ctx, user, items, ctx.l.econ.inv.cats.magic)

    @inventory.group(name="misc", aliases=["other"])
    async def inventory_misc(self, ctx, user: discord.User = None):
        valid, user = await self.inventory_boiler(ctx, user)

        if not valid:
            return

        combined_cats = self.d.cats.tools + self.d.cats.magic + self.d.cats.fish
        items = [e for e in await self.db.fetch_items(user.id) if e["name"] not in combined_cats]

        await self.inventory_logic(ctx, user, items, ctx.l.econ.inv.cats.misc, (16 if len(items) > 24 else 8))

    @inventory.group(name="fish", aliases=["fishes", "fishing", "fishies"])
    async def inventory_fish(self, ctx, user: discord.User = None):
        valid, user = await self.inventory_boiler(ctx, user)

        if not valid:
            return

        items = [e for e in await self.db.fetch_items(user.id) if e["name"] in self.d.cats.fish]

        await self.inventory_logic(ctx, user, items, ctx.l.econ.inv.cats.fish)

    @commands.command(name="deposit", aliases=["dep"])
    # @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def vault_deposit(self, ctx, emerald_blocks: str):
        """Deposits the given amount of emerald blocks into the vault"""

        db_user = await self.db.fetch_user(ctx.author.id)

        c_v_bal = db_user["vault_balance"]
        c_v_max = db_user["vault_max"]
        c_bal = db_user["emeralds"]

        if c_bal < 9:
            await self.bot.reply_embed(ctx, ctx.l.econ.dep.poor_loser)
            return

        if emerald_blocks.lower() in ("all", "max"):
            amount = c_v_max - c_v_bal

            if amount * 9 > c_bal:
                amount = math.floor(c_bal / 9)
        else:
            try:
                amount = int(emerald_blocks)
            except ValueError:
                await self.bot.reply_embed(ctx, ctx.l.econ.use_a_number_stupid)
                return

        if amount * 9 > c_bal:
            await self.bot.reply_embed(ctx, ctx.l.econ.dep.stupid_3)
            return

        if amount < 1:
            if emerald_blocks.lower() in ("all", "max"):
                await self.bot.reply_embed(ctx, ctx.l.econ.dep.stupid_2)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.dep.stupid_1)

            return

        if amount > c_v_max - c_v_bal:
            await self.bot.reply_embed(ctx, ctx.l.econ.dep.stupid_2)
            return

        await self.db.balance_sub(ctx.author.id, amount * 9)
        await self.db.set_vault(ctx.author.id, c_v_bal + amount, c_v_max)

        await self.bot.reply_embed(
            ctx, ctx.l.econ.dep.deposited.format(amount, self.d.emojis.emerald_block, amount * 9, self.d.emojis.emerald)
        )

    @commands.command(name="withdraw", aliases=["with"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def vault_withdraw(self, ctx, emerald_blocks: str):
        """Withdraws a certain amount of emerald blocks from the vault"""

        db_user = await self.db.fetch_user(ctx.author.id)

        c_v_bal = db_user["vault_balance"]
        c_v_max = db_user["vault_max"]

        if c_v_bal < 1:
            await self.bot.reply_embed(ctx, ctx.l.econ.withd.poor_loser)
            return

        if emerald_blocks.lower() in ("all", "max"):
            amount = c_v_bal
        else:
            try:
                amount = int(emerald_blocks)
            except ValueError:
                await self.bot.reply_embed(ctx, ctx.l.econ.use_a_number_stupid)
                return

        if amount < 1:
            await self.bot.reply_embed(ctx, ctx.l.econ.withd.stupid_1)
            return

        if amount > c_v_bal:
            await self.bot.reply_embed(ctx, ctx.l.econ.withd.stupid_2)
            return

        await self.db.balance_add(ctx.author.id, amount * 9)
        await self.db.set_vault(ctx.author.id, c_v_bal - amount, c_v_max)

        await self.bot.reply_embed(
            ctx, ctx.l.econ.withd.withdrew.format(amount, self.d.emojis.emerald_block, amount * 9, self.d.emojis.emerald)
        )

    @commands.group(name="shop")
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def shop(self, ctx):
        """Shows the available options in the Villager Shop"""

        if ctx.invoked_subcommand is None:
            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=ctx.l.econ.shop.villager_shop, icon_url=self.d.splash_logo)

            # row 1
            embed.add_field(
                name=f"__**{ctx.l.econ.shop.tools.format(self.d.emojis.netherite_pickaxe_ench)}**__",
                value=f"`{ctx.prefix}shop tools`",
            )
            embed.add_field(name="\uFEFF", value="\uFEFF")
            embed.add_field(
                name=f"__**{ctx.l.econ.shop.magic.format(self.d.emojis.enchanted_book)}**__", value=f"`{ctx.prefix}shop magic`"
            )

            # row 2
            embed.add_field(
                name=f"__**{ctx.l.econ.shop.other.format(self.d.emojis.totem)}**__", value=f"`{ctx.prefix}shop other`"
            )
            embed.add_field(name="\uFEFF", value="\uFEFF")
            embed.add_field(
                name=f"__**{ctx.l.econ.shop.fish.format(self.d.emojis.fish.cod)}**__", value=f"`{ctx.prefix}shop fish`"
            )

            embed.set_footer(text=ctx.l.econ.shop.embed_footer.format(ctx.prefix))

            await ctx.reply(embed=embed, mention_author=False)

    async def shop_logic(self, ctx, _type, header):
        items = []

        # filter out items which aren't of the right _type
        for item in [self.d.shop_items[key] for key in self.d.shop_items.keys()]:
            if item.cat == _type:
                items.append(item)

        items_sorted = sorted(items, key=(lambda item: item.buy_price))  # sort by buy price
        items_chunked = [items_sorted[i : i + 4] for i in range(0, len(items_sorted), 4)]  # split into chunks of 4

        page = 0
        page_max = len(items_chunked)

        msg = None

        while True:
            embed = discord.Embed(color=self.d.cc)
            embed.set_author(name=header, icon_url=self.d.splash_logo)

            for item in items_chunked[page]:
                embed.add_field(
                    name=f"{item.db_entry[0]} ({format_required(self.d, item)})",
                    value=f"`{ctx.prefix}buy {item.db_entry[0].lower()}`",
                    inline=False,
                )

            embed.set_footer(text=f"{ctx.l.econ.page} {page+1}/{page_max}")

            if msg is None:
                msg = await ctx.reply(embed=embed, mention_author=False)
            else:
                if not msg.embeds[0] == embed:
                    await msg.edit(embed=embed)

            if page_max <= 1:
                return

            await asyncio.sleep(0.25)
            await msg.add_reaction("⬅️")
            await asyncio.sleep(0.25)
            await msg.add_reaction("➡️")

            try:

                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                # wait for reaction from message author (1 min)
                react, r_user = await self.bot.wait_for("reaction_add", check=author_check, timeout=60)
            except asyncio.TimeoutError:
                return

            await react.remove(ctx.author)

            if react.emoji == "⬅️":
                page -= 1
            elif react.emoji == "➡️":
                page += 1

            if page > page_max - 1:
                page = page_max - 1

            if page < 0:
                page = 0

            await asyncio.sleep(0.2)

    @shop.command(name="tools")
    async def shop_tools(self, ctx):
        """Allows you to shop for tools"""

        await self.shop_logic(ctx, "tools", f"{ctx.l.econ.shop.villager_shop} [{ctx.l.econ.shop.tools[3:]}]")

    @shop.command(name="magic")
    async def shop_magic(self, ctx):
        """Allows you to shop for magic items"""

        await self.shop_logic(ctx, "magic", f"{ctx.l.econ.shop.villager_shop} [{ctx.l.econ.shop.magic[3:]}]")

    @shop.command(name="other")
    async def shop_other(self, ctx):
        """Allows you to shop for other/miscellaneous items"""

        await self.shop_logic(ctx, "other", f"{ctx.l.econ.shop.villager_shop} [{ctx.l.econ.shop.other[3:]}]")

    @shop.command(name="fish")
    async def shop_fish(self, ctx):
        await self.fish_market(ctx)

    @commands.command(name="fishmarket", aliases=["fishshop", "fishprices", "fishprice"])
    async def fish_market(self, ctx):
        embed_template = discord.Embed(
            color=self.d.cc,
            title=ctx.l.econ.fishing.market.title.format(self.d.emojis.fish.cod, self.d.emojis.fish.rainbow_trout),
            description=ctx.l.econ.fishing.market.desc,
        )

        fields = []

        for i, fish in enumerate(self.d.fishing.fish.items()):
            fish_id, fish = fish

            fields.append(
                {
                    "name": f"{self.d.emojis.fish[fish_id]} {fish.name}",
                    "value": ctx.l.econ.fishing.market.current.format(fish.current, self.d.emojis.emerald),
                }
            )

            if i % 2 == 0:
                fields.append({"name": "\uFEFF", "value": "\uFEFF"})

            await asyncio.sleep(0)

        groups = [fields[i : i + 6] for i in range(0, len(fields), 6)]
        page_max = len(groups)
        page = 0
        msg = None

        while True:
            embed = embed_template.copy()

            for field in groups[page]:
                embed.add_field(**field)

            embed.set_footer(text=f"{ctx.l.econ.page} {page+1}/{page_max}")

            if msg is None:
                msg = await ctx.reply(embed=embed, mention_author=False)
            elif not msg.embeds[0] == embed:
                await msg.edit(embed=embed)

            if page_max <= 1:
                return

            await asyncio.sleep(0.25)
            await msg.add_reaction("⬅️")
            await asyncio.sleep(0.25)
            await msg.add_reaction("➡️")

            try:

                def author_check(react, r_user):
                    return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                # wait for reaction from message author (1 min)
                react, r_user = await self.bot.wait_for("reaction_add", check=author_check, timeout=60)
            except asyncio.TimeoutError:
                return

            await react.remove(ctx.author)

            if react.emoji == "⬅️":
                page -= 1
            elif react.emoji == "➡️":
                page += 1

            if page > page_max - 1:
                page = page_max - 1

            if page < 0:
                page = 0

            await asyncio.sleep(0.2)

    @commands.command(name="buy", aliases=["purchase"])
    # @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def buy(self, ctx, *, amount_item):
        """Allows you to buy items"""

        amount_item = amount_item.lower()
        db_user = await self.db.fetch_user(ctx.author.id)

        if amount_item.startswith("max ") or amount_item.startswith("all "):
            item = amount_item[4:]

            try:
                amount = math.floor(db_user["emeralds"] / self.d.shop_items[item].buy_price)
            except KeyError:
                await self.bot.reply_embed(ctx, ctx.l.econ.buy.stupid_2.format(item))
                return

            if amount < 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.buy.poor_loser_1)
                return
        else:
            split = amount_item.split(" ")

            try:
                amount = split.pop(0)
                amount = int(amount)
            except ValueError:
                item = amount
                item += (" " + " ".join(split)) if len(split) > 0 else ""
                amount = 1
            else:
                item = " ".join(split)

        if amount < 1:
            await self.bot.reply_embed(ctx, ctx.l.econ.buy.stupid_1)
            return

        shop_item = self.d.shop_items.get(item)

        # shop item doesn't exist lol
        if shop_item is None:
            await self.bot.reply_embed(ctx, ctx.l.econ.buy.stupid_2.format(item))
            return

        # check if user can actually afford to buy that amount of that item
        if shop_item.buy_price * amount > db_user["emeralds"]:
            await self.bot.reply_embed(ctx, ctx.l.econ.buy.poor_loser_2.format(amount, shop_item.db_entry[0]))
            return

        db_item = await self.db.fetch_item(ctx.author.id, shop_item.db_entry[0])

        # get count of item in db for that user
        if db_item is not None:
            db_item_count = db_item["amount"]
        else:
            db_item_count = 0

        # if they already have hit the limit on how many they can buy of that item
        count_lt = shop_item.requires.get("count_lt")
        if count_lt is not None and count_lt < db_item_count + amount:
            await self.bot.reply_embed(ctx, ctx.l.econ.buy.no_to_item_1)
            return

        # ensure user has required items
        for req_item, req_amount in shop_item.requires.get("items", {}).items():
            db_req_item = await self.db.fetch_item(ctx.author.id, req_item)

            if db_req_item is None or db_req_item["amount"] < req_amount:
                await self.bot.reply_embed(
                    ctx, ctx.l.econ.buy.need_total_of.format(req_amount, req_item, self.d.emojis[self.d.emoji_items[req_item]])
                )
                return

        await self.db.balance_sub(ctx.author.id, shop_item.buy_price * amount)

        for req_item, req_amount in shop_item.requires.get("items", {}).items():
            await self.db.remove_item(ctx.author.id, req_item, req_amount * amount)

        await self.db.add_item(ctx.author.id, shop_item.db_entry[0], shop_item.db_entry[1], amount, shop_item.db_entry[2])

        if shop_item.db_entry[0].endswith("Pickaxe") or shop_item.db_entry[0] == "Bane Of Pillagers Amulet":
            member = self.bot.get_guild(self.d.support_server_id).get_member(ctx.author.id)

            if member is not None:
                await self.bot.update_support_member_role(member)

        if shop_item.db_entry[0] == "Rich Person Trophy":
            await self.db.rich_trophy_wipe(ctx.author.id)

        await self.bot.reply_embed(
            ctx,
            ctx.l.econ.buy.you_done_bought.format(
                amount, shop_item.db_entry[0], format_required(self.d, shop_item, amount), amount + db_item_count
            ),
        )

    @commands.command(name="sell", aliases=["emeraldify"])
    # @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def sell(self, ctx, *, amount_item):
        """Allows you to sell items"""

        amount_item = amount_item.lower()

        if amount_item.startswith("max ") or amount_item.startswith("all "):
            item = amount_item[4:]
            db_item = await self.db.fetch_item(ctx.author.id, item)

            if db_item is None:
                await self.bot.reply_embed(ctx, ctx.l.econ.sell.invalid_item)
                return

            amount = db_item["amount"]
        else:
            split = amount_item.split(" ")

            try:
                amount = split.pop(0)
                amount = int(amount)
            except ValueError:
                item = amount
                item += (" " + " ".join(split)) if len(split) > 0 else ""
                amount = 1
            else:
                item = " ".join(split)

            db_item = await self.db.fetch_item(ctx.author.id, item)

        if db_item is None:
            await self.bot.reply_embed(ctx, ctx.l.econ.sell.invalid_item)
            return

        if not db_item["sellable"]:
            await self.bot.reply_embed(ctx, ctx.l.econ.sell.stupid_3)
            return

        if amount > db_item["amount"]:
            await self.bot.reply_embed(ctx, ctx.l.econ.sell.stupid_1)
            return

        if amount < 1:
            await self.bot.reply_embed(ctx, ctx.l.econ.sell.stupid_2)
            return

        for fish_id, fish in self.d.fishing.fish.items():
            if db_item["name"] == fish.name:
                db_item = {**db_item, "sell_price": fish.current}

        await self.db.balance_add(ctx.author.id, amount * db_item["sell_price"])
        await self.db.remove_item(ctx.author.id, db_item["name"], amount)

        if db_item["name"].endswith("Pickaxe") or db_item["name"] == "Bane Of Pillagers Amulet":
            member = self.bot.get_guild(self.d.support_server_id).get_member(ctx.author.id)

            if member is not None:
                await self.bot.update_support_member_role(member)

        await self.bot.reply_embed(
            ctx,
            ctx.l.econ.sell.you_done_sold.format(
                amount, db_item["name"], amount * db_item["sell_price"], self.d.emojis.emerald
            ),
        )

    @commands.command(name="give", aliases=["gift", "share", "gib"])
    @commands.before_invoke(lock_author)
    @commands.after_invoke(unlock_author)
    @commands.guild_only()
    # @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def give(self, ctx, user: discord.Member, *, amount_item):
        """Give an item or emeralds to another person"""

        if user.bot:
            if user.id == self.bot.user.id:
                await self.bot.reply_embed(ctx, ctx.l.econ.give.bot_1)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.give.bot_2)
            return

        if ctx.author.id == user.id:
            await self.bot.reply_embed(ctx, ctx.l.econ.give.stupid_1)
            return

        async with self._user_locks[user.id]:
            amount_item = amount_item.lower()
            try:
                # to be given is emeralds
                amount = int(amount_item)
                item = "emerald"
            except Exception:
                split = amount_item.split(" ")
                try:
                    temp_split = split.copy()
                    amount = int(temp_split.pop(0))
                    split = temp_split

                except Exception:
                    amount = 1

                item = " ".join(split)

            if amount < 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.give.stupid_2)
                return

            db_user = await self.db.fetch_user(ctx.author.id)

            if "pickaxe" in item.lower() or "sword" in item.lower():
                await self.bot.reply_embed(ctx, ctx.l.econ.give.and_i_oop)
                return

            if item in ("emerald", "emeralds", ":emerald:"):
                if amount > db_user["emeralds"]:
                    await self.bot.reply_embed(ctx, ctx.l.econ.give.stupid_3)
                    return

                await self.db.balance_sub(ctx.author.id, amount)
                await self.db.balance_add(user.id, amount)
                await self.db.log_transaction("emerald", amount, arrow.utcnow().datetime, ctx.author.id, user.id)

                await self.bot.reply_embed(
                    ctx, ctx.l.econ.give.gaveems.format(ctx.author.mention, amount, self.d.emojis.emerald, user.mention)
                )

                if (await self.db.fetch_user(user.id))["give_alert"]:
                    await self.bot.send_embed(
                        user, ctx.l.econ.give.gaveyouems.format(ctx.author.mention, amount, self.d.emojis.emerald)
                    )
            else:
                db_item = await self.db.fetch_item(ctx.author.id, item)

                if db_item is None or amount > db_item["amount"]:
                    await self.bot.reply_embed(ctx, ctx.l.econ.give.stupid_4)
                    return

                if db_item["sticky"]:
                    await self.bot.reply_embed(ctx, ctx.l.econ.give.and_i_oop)
                    return

                if amount < 1:
                    await self.bot.reply_embed(ctx, ctx.l.econ.give.stupid_2)
                    return

                await self.db.remove_item(ctx.author.id, item, amount)
                await self.db.add_item(user.id, db_item["name"], db_item["sell_price"], amount)
                self.bot.loop.create_task(
                    self.db.log_transaction(db_item["name"], amount, arrow.utcnow().datetime, ctx.author.id, user.id)
                )

                await self.bot.reply_embed(
                    ctx, ctx.l.econ.give.gave.format(ctx.author.mention, amount, db_item["name"], user.mention)
                )

                if (await self.db.fetch_user(user.id))["give_alert"]:
                    await self.bot.send_embed(
                        user, ctx.l.econ.give.gaveyou.format(ctx.author.mention, amount, db_item["name"])
                    )

    @commands.command(name="gamble", aliases=["bet", "stonk", "stonks"])
    # @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def gamble(self, ctx, amount):
        """Gamble for emeralds with Villager Bot"""

        db_user = await self.db.fetch_user(ctx.author.id)

        if amount.lower() in ("all", "max"):
            amount = db_user["emeralds"]

        else:
            try:
                amount = int(amount)
            except ValueError:
                await self.bot.reply_embed(ctx, ctx.l.econ.use_a_number_stupid)
                return

        if amount > db_user["emeralds"]:
            await self.bot.reply_embed(ctx, ctx.l.econ.gamble.stupid_1)
            return

        if amount < 10:
            await self.bot.reply_embed(ctx, ctx.l.econ.gamble.stupid_2)
            return

        if amount > 50000:
            await self.bot.reply_embed(ctx, ctx.l.econ.gamble.stupid_3)
            return

        if db_user["emeralds"] >= 200000:
            await self.bot.reply_embed(ctx, ctx.l.econ.gamble.too_rich)
            return

        u_roll = random.randint(1, 6) + random.randint(1, 6)
        b_roll = random.randint(1, 6) + random.randint(1, 6)

        await self.bot.reply_embed(ctx, ctx.l.econ.gamble.roll.format(u_roll, b_roll))

        if u_roll > b_roll:
            multi = (
                40
                + random.randint(5, 30)
                + (await self.db.fetch_item(ctx.author.id, "Bane Of Pillagers Amulet") is not None) * 20
            )
            multi += (await self.db.fetch_item(ctx.author.id, "Rich Person Trophy") is not None) * 40
            multi = (150 + random.randint(-5, 0)) if multi >= 150 else multi
            multi /= 100

            won = multi * amount
            won = math.ceil(min(won, math.log(won, 1.001)))

            await self.db.balance_add(ctx.author.id, won)
            await self.bot.reply_embed(
                ctx, ctx.l.econ.gamble.win.format(random.choice(ctx.l.econ.gamble.actions), won, self.d.emojis.emerald)
            )
        elif u_roll < b_roll:
            await self.db.balance_sub(ctx.author.id, amount)
            await self.bot.reply_embed(ctx, ctx.l.econ.gamble.lose.format(amount, self.d.emojis.emerald))
        else:
            await self.bot.reply_embed(ctx, ctx.l.econ.gamble.tie)

    @commands.command(name="search", aliases=["beg"])
    # @commands.cooldown(1, 30 * 60, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def search(self, ctx):
        """Beg for emeralds"""

        db_user = await self.db.fetch_user(ctx.author.id)

        if random.choice([True, True, True, True, True, False]) or db_user["emeralds"] < 2:
            if random.randint(1, 420) == 420:
                mooderalds = random.randint(1, 3)
                await self.db.add_item(ctx.author.id, "Mooderald", 768, mooderalds)
                await self.bot.reply_embed(
                    ctx, random.choice(ctx.l.econ.beg.mooderald).format(f"{mooderalds}{self.d.emojis.autistic_emerald}")
                )

            else:
                amount = 9 + math.ceil(math.log(db_user["emeralds"] + 1, 1.5)) + random.randint(1, 5)
                amount = random.randint(1, 4) if amount < 1 else amount

                await self.db.balance_add(ctx.author.id, amount)

                await self.bot.reply_embed(
                    ctx, random.choice(ctx.l.econ.beg.positive).format(f"{amount}{self.d.emojis.emerald}")
                )
        else:
            amount = 9 + math.ceil(math.log(db_user["emeralds"] + 1, 1.3)) + random.randint(1, 5)  # ah yes, meth

            if amount < 1:
                amount = random.randint(1, 4)
            elif amount > 45000:
                amount = 45000 + random.randint(0, abs(int((amount - 45000)) / 3) + 1)

            if db_user["emeralds"] < amount:
                amount = db_user["emeralds"]

            await self.db.balance_sub(ctx.author.id, amount)

            await self.bot.reply_embed(ctx, random.choice(ctx.l.econ.beg.negative).format(f"{amount}{self.d.emojis.emerald}"))

    @commands.command(name="mine", aliases=["mein", "eun", "mien"])
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def mine(self, ctx):
        if not await self.math_problem(ctx):
            return

        pickaxe = await self.db.fetch_pickaxe(ctx.author.id)

        # calculate if user finds emeralds OR not
        found = random.choice(self.calc_yield_chance_list(pickaxe))

        # ~~what the fuck?~~
        # calculate bonus emeralds from enchantment items
        if found:
            for item in self.d.mining.yields_enchant_items.keys():
                if await self.db.fetch_item(ctx.author.id, item) is not None:
                    found += random.choice(self.d.mining.yields_enchant_items[item])
                    break

            await asyncio.sleep(0)

        if not found:
            for item in self.d.mining.findables:  # try to see if user gets an item
                if random.randint(0, item[2]) == 1:
                    await self.db.add_item(ctx.author.id, item[0], item[1], 1, item[3])

                    await self.bot.reply_embed(
                        ctx,
                        f"{self.d.emojis[self.d.emoji_items[pickaxe]]} \uFEFF "
                        + ctx.l.econ.mine.found_item_1.format(
                            random.choice(ctx.l.econ.mine.actions),
                            1,
                            item[0],
                            item[1],  # shhhhh ignore the pep8 violations and move on
                            self.d.emojis.emerald,
                            random.choice(ctx.l.econ.mine.places),
                        ),
                    )

                    return

                await asyncio.sleep(0)

            # only works cause num of pickaxes is 6 and levels of fake finds is 3
            # please don't bug me about jank code, I know
            fake_finds = self.d.mining.finds[math.floor(self.d.mining.pickaxes.index(pickaxe) / 2)]

            await self.bot.reply_embed(
                ctx,
                f"{self.d.emojis[self.d.emoji_items[pickaxe]]} \uFEFF "
                + ctx.l.econ.mine.found_item_2.format(
                    random.choice(ctx.l.econ.mine.actions),
                    random.randint(1, 6),
                    random.choice(ctx.l.econ.mine.useless),
                    random.choice(fake_finds),
                ),
            )
        else:
            found = int(found)

            if await self.db.fetch_item(ctx.author.id, "Rich Person Trophy") is not None:
                found *= 2

            await self.db.balance_add(ctx.author.id, found)

            await self.bot.reply_embed(
                ctx,
                f"{self.d.emojis[self.d.emoji_items[pickaxe]]} \uFEFF "
                + ctx.l.econ.mine.found_emeralds.format(random.choice(ctx.l.econ.mine.actions), found, self.d.emojis.emerald),
            )

        if random.randint(0, 50) == 1:
            db_user = await self.db.fetch_user(ctx.author.id)
            if db_user["vault_max"] < 2000:
                await self.db.update_user(ctx.author.id, vault_max=(db_user["vault_max"] + 1))

    @commands.command(name="fish", aliases=["phish", "feesh"])
    @commands.guild_only()
    # @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def fish(self, ctx):
        if not await self.math_problem(ctx, 5):
            return

        if await self.db.fetch_item(ctx.author.id, "Fishing Rod") is None:
            await self.bot.reply_embed(ctx, ctx.l.econ.fishing.stupid_1)
            return

        await self.bot.reply_embed(ctx, random.choice(ctx.l.econ.fishing.cast))

        async with ctx.typing():
            wait = random.randint(8, 20)

            if await self.db.fetch_item(ctx.author.id, "Lure I Book") is not None:
                wait -= 2

            if "seaweed" in self.v.chuggers.get(ctx.author.id, []):
                wait -= 2

            await asyncio.sleep(wait)

        # fished up item or junk or somethin not fish
        if random.randint(1, 8) == 1:
            junk_chance = (True, True, True, True, False)

            if await self.db.fetch_item(ctx.author.id, "Fishing Trophy") is not None:
                junk_chance = (True, True, True, False, False, False)

            if random.choice(junk_chance):  # junk
                junk = random.choice(ctx.l.econ.fishing.junk)
                await self.bot.reply_embed(ctx, junk, True)

                if "meme" in junk:
                    await self.bot.get_cog("Fun").meme(ctx)

                return

            while True:
                for item in self.d.fishing.findables:
                    if random.randint(0, (item[2] // 2) + 2) == 1:
                        await self.db.add_item(ctx.author.id, item[0], item[1], 1, item[3])
                        await self.bot.reply_embed(
                            ctx,
                            random.choice(ctx.l.econ.fishing.item).format(item[0], item[1], self.d.emojis.emerald),
                            True,
                        )
                        return

                    await asyncio.sleep(0)

        fish_id = random.choices(self.d.fishing.fish_ids, self.d.fishing.fish_weights)[0]
        fish = self.d.fishing.fish[fish_id]

        await self.db.add_item(ctx.author.id, fish.name, -1, 1)
        await self.bot.reply_embed(
            ctx, random.choice(ctx.l.econ.fishing.caught).format(fish.name, self.d.emojis.fish[fish_id]), True
        )

        await self.db.update_lb(ctx.author.id, "fish", 1, "add")

        if random.randint(0, 50) == 1:
            db_user = await self.db.fetch_user(ctx.author.id)

            if db_user["vault_max"] < 2000:
                await self.db.update_user(ctx.author.id, vault_max=(db_user["vault_max"] + 1))

    @commands.command(name="pillage", aliases=["rob", "mug"])
    @commands.before_invoke(lock_author)
    @commands.after_invoke(unlock_author)
    @commands.guild_only()
    # @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def pillage(self, ctx, victim: discord.Member):
        if victim.bot:
            if victim.id == self.bot.user.id:
                await self.bot.reply_embed(ctx, ctx.l.econ.pillage.bot_1)
            else:
                await self.bot.reply_embed(ctx, ctx.l.econ.pillage.bot_2)
            return

        if ctx.author.id == victim.id:
            await self.bot.reply_embed(ctx, ctx.l.econ.pillage.stupid_1)
            return

        if ctx.guild.get_member(victim.id) is None:
            await self.bot.reply_embed(ctx, ctx.l.econ.pillage.stupid_2)
            return

        async with self._user_locks[victim.id]:
            db_user = await self.db.fetch_user(ctx.author.id)

            if db_user["emeralds"] < 64:
                await self.bot.reply_embed(ctx, ctx.l.econ.pillage.stupid_3.format(self.d.emojis.emerald))
                return

            db_victim = await self.db.fetch_user(victim.id)

            if db_victim["emeralds"] < 64:
                await self.bot.reply_embed(ctx, ctx.l.econ.pillage.stupid_4.format(self.d.emojis.emerald))
                return

            pillager_pillages = self.v.pillagers.get(ctx.author.id, 0)
            self.v.pillagers[ctx.author.id] = pillager_pillages + 1

            times_pillaged = self.v.pillages.get(victim.id, 0)
            self.v.pillages[victim.id] = times_pillaged + 1

            user_bees = await self.db.fetch_item(ctx.author.id, "Jar Of Bees")
            user_bees = 0 if user_bees is None else user_bees["amount"]

            victim_bees = await self.db.fetch_item(victim.id, "Jar Of Bees")
            victim_bees = 0 if victim_bees is None else victim_bees["amount"]

            # lmao
            if pillager_pillages > 7 or times_pillaged > 4:
                chances = [False] * 50 + [True]
            elif await self.db.fetch_item(victim.id, "Bane Of Pillagers Amulet"):
                chances = [False] * 5 + [True]
            elif user_bees > victim_bees:
                chances = [False] * 3 + [True] * 5
            elif user_bees < victim_bees:
                chances = [False] * 5 + [True] * 3
            else:
                chances = [True, False]

            pillager_sword_lvl = self.d.sword_list.index((await self.db.fetch_sword(ctx.author.id)).lower())
            victim_sword_lvl = self.d.sword_list.index((await self.db.fetch_sword(victim.id)).lower())

            if pillager_sword_lvl > victim_sword_lvl:
                chances.append(True)
            elif pillager_sword_lvl < victim_sword_lvl:
                chances.append(False)

            success = random.choice(chances)

            if success:
                # calculate base stolen value
                stolen = math.ceil(db_victim["emeralds"] * (random.randint(10, 40) / 100))
                # calculate and implement cap based off pillager's balance
                stolen = min(stolen, math.ceil(db_user["emeralds"] ** 1.1 + db_user["emeralds"] * 5) + random.randint(1, 10))

                # 8% tax to prevent exploitation of pillaging leaderboard
                adjusted = math.ceil(stolen * 0.92)  # villager bot will steal ur stuff hehe

                await self.db.balance_sub(victim.id, stolen)
                await self.db.balance_add(ctx.author.id, adjusted)  # 8% tax

                await self.bot.reply_embed(
                    ctx, random.choice(ctx.l.econ.pillage.u_win.user).format(adjusted, self.d.emojis.emerald)
                )
                await self.bot.send_embed(
                    victim,
                    random.choice(ctx.l.econ.pillage.u_win.victim).format(ctx.author.mention, stolen, self.d.emojis.emerald),
                )

                await self.db.update_lb(ctx.author.id, "pillages", adjusted, "add")
            else:
                penalty = max(32, db_user["emeralds"] // 3)

                await self.db.balance_sub(ctx.author.id, penalty)
                await self.db.balance_add(victim.id, penalty)

                await self.bot.reply_embed(
                    ctx, random.choice(ctx.l.econ.pillage.u_lose.user).format(penalty, self.d.emojis.emerald)
                )
                await self.bot.send_embed(victim, random.choice(ctx.l.econ.pillage.u_lose.victim).format(ctx.author.mention))

    @commands.command(name="use", aliases=["eat", "chug", "smoke"])
    # @commands.cooldown(1, 2, commands.BucketType.user)
    async def use_item(self, ctx, *, thing):
        """Allows you to use potions and some other items"""

        thing = thing.lower()
        split = thing.split()

        try:
            amount = int(split[0])
            thing = " ".join(split[1:])
        except (IndexError, ValueError):
            amount = 1

        if amount < 1:
            await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_3)
            return

        if amount > 100:
            await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_4)
            return

        current_pots = await self.ipc.eval(f"active_effects[{ctx.author.id}]")

        if thing in current_pots:
            await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
            return

        db_item = await self.db.fetch_item(ctx.author.id, thing)

        if db_item is None:
            await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_2)
            return

        if db_item["amount"] < amount:
            await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_5)
            return

        if thing == "haste i potion":
            if amount > 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
                return

            await self.db.remove_item(ctx.author.id, thing, 1)
            await self.ipc.eval(f"active_effects[{ctx.author.id}].add('haste i potion')")
            await self.bot.reply_embed(ctx, ctx.l.econ.use.chug.format("Haste I Potion", 6))

            await asyncio.sleep(60 * 6)

            await self.bot.send_embed(ctx.author, ctx.l.econ.use.done.format("Haste I Potion"))
            await self.ipc.eval(f"active_effects[{ctx.author.id}].remove('haste i potion')")
            return

        if thing == "haste ii potion":
            if amount > 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
                return

            await self.db.remove_item(ctx.author.id, thing, 1)
            await self.ipc.eval(f"active_effects[{ctx.author.id}].add('haste ii potion')")
            await self.bot.reply_embed(ctx, ctx.l.econ.use.chug.format("Haste II Potion", 4.5))

            await asyncio.sleep(60 * 4.5)

            await self.bot.send_embed(ctx.author, ctx.l.econ.use.done.format("Haste II Potion"))
            await self.ipc.eval(f"active_effects[{ctx.author.id}].remove('haste ii potion')")
            return

        if thing == "seaweed":
            if amount > 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
                return

            await self.db.remove_item(ctx.author.id, thing, 1)
            await self.ipc.eval(f"active_effects[{ctx.author.id}].add('seaweed')")
            await self.bot.reply_embed(ctx, ctx.l.econ.use.smoke_seaweed.format(30))

            await asyncio.sleep(60 * 30)

            await self.bot.send_embed(ctx.author, ctx.l.econ.use.seaweed_done)
            await self.ipc.eval(f"active_effects[{ctx.author.id}].remove('seaweed')")
            return

        if thing == "vault potion":
            if amount > 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
                return

            db_user = await self.db.fetch_user(ctx.author.id)

            if db_user["vault_max"] > 1999:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.vault_max)
                return

            add = random.randint(9, 15)

            if db_user["vault_max"] + add > 2000:
                add = 2000 - db_user["vault_max"]

            await self.db.remove_item(ctx.author.id, "Vault Potion", 1)
            await self.db.set_vault(ctx.author.id, db_user["vault_balance"], db_user["vault_max"] + add)

            await self.bot.reply_embed(ctx, ctx.l.econ.use.vault_pot.format(add))
            return

        if thing == "honey jar":
            db_user = await self.db.fetch_user(ctx.author.id)

            max_amount = 20 - db_user["health"]
            if max_amount < 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.cant_use_any.format("Honey Jars"))
                return

            if db_user["health"] + amount > 20:
                amount = max_amount

            await self.db.update_user(ctx.author.id, health=(db_user["health"] + amount))
            await self.db.remove_item(ctx.author.id, "Honey Jar", amount)

            new_health = amount + db_user["health"]
            await self.bot.reply_embed(ctx, ctx.l.econ.use.chug_honey.format(amount, new_health, self.d.emojis.heart_full))

            return

        if thing == "present":
            if amount > 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
                return

            await self.db.remove_item(ctx.author.id, "Present", 1)

            while True:
                for item in self.d.mining.findables:
                    if random.randint(0, (item[2] // 2) + 2) == 1:
                        await self.db.add_item(ctx.author.id, item[0], item[1], 1, item[3])
                        await self.bot.reply_embed(
                            ctx, random.choice(ctx.l.econ.use.present).format(item[0], item[1], self.d.emojis.emerald)
                        )

                        return

                    await asyncio.sleep(0)

        if thing == "barrel":
            if amount > 1:
                await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_1)
                return

            await self.db.remove_item(ctx.author.id, "Barrel", 1)

            for _ in range(20):
                for item in self.d.mining.findables:
                    if item[2] > 1000:
                        if random.randint(0, (item[2] // 1.5) + 5) == 1:
                            await self.db.add_item(ctx.author.id, item[0], item[1], 1, item[3])
                            await self.bot.reply_embed(
                                ctx, random.choice(ctx.l.econ.use.barrel_item).format(item[0], item[1], self.d.emojis.emerald)
                            )

                            return

                    await asyncio.sleep(0)

            ems = random.randint(2, 4096)

            if await self.db.fetch_item(ctx.author.id, "Rich Person Trophy") is not None:
                ems *= 1.5
                ems = round(ems)

            await self.bot.reply_embed(ctx, random.choice(ctx.l.econ.use.barrel_ems).format(ems, self.d.emojis.emerald))
            await self.db.balance_add(ctx.author.id, ems)
            return

        if thing == "glass beaker":
            slime_balls = await self.db.fetch_item(ctx.author.id, "Slime Ball")

            if slime_balls is None or slime_balls["amount"] < amount:
                await ctx.reply_embed(ctx.l.econ.use.need_slimy_balls)
                return

            await self.db.remove_item(ctx.author.id, "Slime Ball", amount)
            await self.db.remove_item(ctx.author.id, "Glass Beaker", amount)
            await self.db.add_item(ctx.author.id, "Beaker Of Slime", 13, amount, False)

            await self.bot.reply_embed(ctx, ctx.l.econ.use.slimy_balls_funne.format(amount))
            return

        if thing == "beaker of slime":
            await self.db.remove_item(ctx.author.id, "Beaker Of Slime", amount)
            await self.db.add_item(ctx.author.id, "Slime Ball", 5, amount, True)

            await self.bot.reply_embed(ctx, ctx.l.econ.use.beaker_of_slime_undo.format(amount))
            return

        await self.bot.reply_embed(ctx, ctx.l.econ.use.stupid_6)

    @commands.command(name="honey", aliases=["harvesthoney", "horny"])  # ~~a strange urge occurs in me~~
    # @commands.cooldown(1, 24 * 60 * 60, commands.BucketType.user)
    async def honey(self, ctx):
        bees = await self.db.fetch_item(ctx.author.id, "Jar Of Bees")

        if bees is not None:
            bees = bees["amount"]
        else:
            bees = 0

        if bees > 1024:
            bees = 1024

        if bees < 100:
            await self.bot.reply_embed(ctx, random.choice(ctx.l.econ.honey.stupid_1))
            ctx.command.reset_cooldown(ctx)
            return

        jars = bees - random.randint(math.ceil(bees / 6), math.ceil(bees / 2))
        await self.db.add_item(ctx.author.id, "Honey Jar", 1, jars)

        await self.bot.reply_embed(ctx, random.choice(ctx.l.econ.honey.honey).format(jars))  # uwu so sticky oWo

        if random.choice([False] * 3 + [True]):
            bees_lost = random.randint(math.ceil(bees / 75), math.ceil(bees / 50))

            await self.db.remove_item(ctx.author.id, "Jar Of Bees", bees_lost)

            await self.bot.reply_embed(ctx, random.choice(ctx.l.econ.honey.ded).format(bees_lost))

    @commands.group(name="leaderboards", aliases=["lb", "lbs", "leaderboard"])
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def leaderboards(self, ctx):
        if ctx.invoked_subcommand is None:
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.title)

            embed.add_field(name=ctx.l.econ.lb.emeralds, value=f"`{ctx.prefix}leaderboard emeralds`")
            embed.add_field(name="\uFEFF", value="\uFEFF")
            embed.add_field(name=ctx.l.econ.lb.stolen, value=f"`{ctx.prefix}leaderboard stolen`")

            embed.add_field(name=ctx.l.econ.lb.kills, value=f"`{ctx.prefix}leaderboard mobkills`")
            embed.add_field(name="\uFEFF", value="\uFEFF")
            embed.add_field(name=ctx.l.econ.lb.bees, value=f"`{ctx.prefix}leaderboard bees`")

            embed.add_field(name=ctx.l.econ.lb.votes, value=f"`{ctx.prefix}leaderboard votes`")
            embed.add_field(name="\uFEFF", value="\uFEFF")
            embed.add_field(name=ctx.l.econ.lb.fish, value=f"`{ctx.prefix}leaderboard fish`")

            embed.add_field(name=ctx.l.econ.lb.mooderalds, value=f"`{ctx.prefix}leaderboard mooderalds`")
            # embed.add_field(name="\uFEFF", value="\uFEFF")

            await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="emeralds", aliases=["ems"])
    async def leaderboard_emeralds(self, ctx):
        async with ctx.typing():
            ems_global, global_u_entry = await self.db.fetch_global_lb_user("emeralds", ctx.author.id)
            ems_local, local_u_entry = await self.db.fetch_local_lb_user(
                "emeralds", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(
                self, ems_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.emerald)
            )
            lb_local = lb_logic(self, ems_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.emerald))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_ems.format(self.d.emojis.emerald_spinn))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="pillages", aliases=["pil", "stolen"])
    async def leaderboard_pillages(self, ctx):
        async with ctx.typing():
            pillages_global, global_u_entry = await self.db.fetch_global_lb("pillaged_emeralds", ctx.author.id)
            pillages_local, local_u_entry = await self.db.fetch_local_lb(
                "pillaged_emeralds", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(
                self, pillages_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.emerald)
            )
            lb_local = lb_logic(
                self, pillages_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.emerald)
            )

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_pil.format(self.d.emojis.emerald))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="mobkills", aliases=["kil", "kills", "kill", "bonk"])
    async def leaderboard_mobkills(self, ctx):
        async with ctx.typing():
            kills_global, global_u_entry = await self.db.fetch_global_lb("mobs_killed", ctx.author.id)
            kills_local, local_u_entry = await self.db.fetch_local_lb(
                "mobs_killed", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(
                self, kills_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.stevegun)
            )
            lb_local = lb_logic(
                self, kills_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.stevegun)
            )

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_kil.format(self.d.emojis.stevegun))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="bees", aliases=["jarofbees", "jarsofbees"])
    async def leaderboard_bees(self, ctx):
        async with ctx.typing():
            bees_global, global_u_entry = await self.db.fetch_global_lb_item("Jar Of Bees", ctx.author.id)
            bees_local, local_u_entry = await self.db.fetch_local_lb_item(
                "Jar Of Bees", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(self, bees_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.bee))
            lb_local = lb_logic(self, bees_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.bee))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_bee.format(self.d.emojis.anibee))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)

    # @leaderboards.command(name="commands", aliases=["cmds"])
    # async def leaderboard_commands(self, ctx):
    #     async with ctx.typing():
    #         lb_global, lb_local = cmds_lb(self, ctx)

    #     embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_cmds.format(":computer:"))
    #     embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
    #     embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

    #     await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="votes", aliases=["votestreaks", "votestreak"])
    async def leaderboard_votes(self, ctx):
        async with ctx.typing():
            votes_global, global_u_entry = await self.db.fetch_global_lb_user("vote_streak", ctx.author.id)
            votes_local, local_u_entry = await self.db.fetch_local_lb_user(
                "vote_streak", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(
                self, votes_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.updoot)
            )
            lb_local = lb_logic(self, votes_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.updoot))

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_votes.format(":fire:"))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="fish", aliases=["fishies", "fishing"])
    async def leaderboard_fish(self, ctx):
        async with ctx.typing():
            fish_global, global_u_entry = await self.db.fetch_global_lb("fish_fished", ctx.author.id)
            fish_local, local_u_entry = await self.db.fetch_local_lb(
                "fish_fished", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(
                self, fish_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.fish.cod)
            )
            lb_local = lb_logic(
                self, fish_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.fish.cod)
            )

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_fish.format(self.d.emojis.fish.rainbow_trout))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)

    @leaderboards.command(name="mooderalds", aliases=["autism", "moods", "mooderald"])
    async def leaderboard_mooderalds(self, ctx):
        async with ctx.typing():
            moods_global, global_u_entry = await self.db.fetch_global_lb_item("Mooderald", ctx.author.id)
            moods_local, local_u_entry = await self.db.fetch_local_lb_item(
                "Mooderald", ctx.author.id, [m.id for m in ctx.guild.members if not m.bot]
            )

            lb_global = lb_logic(
                self, moods_global, global_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.autistic_emerald)
            )
            lb_local = lb_logic(
                self, moods_local, local_u_entry, "\n`{0}.` **{0}**{1} {0}".format("{}", self.d.emojis.autistic_emerald)
            )

        embed = discord.Embed(color=self.d.cc, title=ctx.l.econ.lb.lb_moods.format(self.d.emojis.autistic_emerald))
        embed.add_field(name=ctx.l.econ.lb.local_lb, value=lb_local)
        embed.add_field(name=ctx.l.econ.lb.global_lb, value=lb_global)

        await ctx.reply(embed=embed, mention_author=False)


def setup(bot):
    bot.add_cog(Econ(bot))
