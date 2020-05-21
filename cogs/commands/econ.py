from discord.ext import commands
import discord
import asyncio
from random import choice, randint
from math import floor, ceil


class Econ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.g = self.bot.get_cog("Global")
        self.db = self.bot.get_cog("Database")

        self.who_is_mining = {}
        self.items_in_use = {}

        self.emerald = "<:emerald:653729877698150405>"

    async def problem(self, ctx):
        if ctx.author.id in self.who_is_mining.keys():
            self.who_is_mining[ctx.author.id] += 1
            if self.who_is_mining[ctx.author.id] >= 101:
                prob = f"{randint(0, 25)}+{randint(0, 25)}"
                prob = [prob, str(eval(prob))]
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Please solve this problem to continue: ``{prob[0]}``"))
                try:
                    msg = await self.bot.wait_for("message", timeout=15)
                    while msg.author.id is not ctx.author.id or msg.channel.id != ctx.channel.id:
                        msg = await self.bot.wait_for("message", timeout=15)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You ran out of time."))
                    return False
                if msg.clean_content == prob[1]:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Correct answer!"))
                    self.who_is_mining[ctx.author.id] = 0
                    return False
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Incorrect answer."))
                    return False
            return True
        else:
            self.who_is_mining[ctx.author.id] = 1
            return True

    @commands.command(name="bal", aliases=["balance"])
    async def balance(self, ctx, user: discord.User=None):
        if user is None:
            user = ctx.author
        if user.bot:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Remember, bot's don't have any rights, and as a result can't possess currency."))
            return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{user.mention} has {await self.db.get_balance(user.id)}{self.emerald}"))

    @commands.command(name="deposit", aliases=["dep"])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def deposit(self, ctx, amount: str):  # In blocks
        their_bal = await self.db.get_balance(ctx.author.id)
        if their_bal < 9:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to deposit!"))
            return
        vault = await self.db.get_vault(ctx.author.id)
        if amount.lower() == "all" or amount.lower() == "max":
            amount = vault[1]-vault[0]
            if floor(their_bal/9) < amount:
                amount = floor(their_bal/9)
        else:
            try:
                amount = int(amount)
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Try using an actual number, idiot!"))
                return

        if vault[1] == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="There isn't enough space in your vault!"))
            return
        if vault[1]-vault[0] <= 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="There isn't enough space in your vault!"))
            return
        if amount*9 > their_bal:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't deposit more emeralds than you have!"))
            return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to deposit one or more emerald blocks at once!"))
            return

        await self.db.set_balance(ctx.author.id, their_bal - (9 * amount))
        await self.db.set_vault(ctx.author.id, vault[0] + amount, vault[1])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have deposited {amount} emerald blocks into the vault. ({amount*9}{self.emerald})"))

    @commands.command(name="withdraw", aliases=["with"])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def withdraw(self, ctx, amount: str): # In emerald blocks
        vault = await self.db.get_vault(ctx.author.id)
        if vault[0] < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have any emerald blocks to withdraw!"))
            return
        if str(amount).lower() == "all" or str(amount).lower() == "max":
            amount = vault[0]
        else:
            try:
                amount = int(amount)
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Try using an actual number, idiot!"))
                return

        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to withdraw one or more emerald blocks at once!"))
            return
        if amount > vault[0]:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't withdraw more emerald blocks than you have!"))
            return

        await self.db.set_balance(ctx.author.id, await self.db.get_balance(ctx.author.id) + (9 * amount))
        await self.db.set_vault(ctx.author.id, vault[0] - amount, vault[1])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have withdrawn {amount} emerald blocks from the vault. ({amount*9}{self.emerald})"))

    @commands.group(name="shop")
    async def shop(self, ctx):
        if ctx.invoked_subcommand is None:
            shop = discord.Embed(color=discord.Color.green())
            shop.set_author(name="Villager Shop", url=discord.Embed.Empty, icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
            shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
            shop.add_field(name="__**Pickaxes**__", value=f"``{ctx.prefix}shop pickaxes``")
            shop.add_field(name="__**Magic Items**__", value=f"``{ctx.prefix}shop magic``")
            shop.add_field(name="__**Other**__", value=f"``{ctx.prefix}shop other``")
            await ctx.send(embed=shop)

    @shop.command(name="pickaxes")
    async def shop_pickaxes(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop [Pickaxes]", url=discord.Embed.Empty, icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
        shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
        shop.add_field(name=f"__**Stone Pickaxe**__ 32{self.emerald}", value=f"``{ctx.prefix}buy stone pickaxe``", inline=True)
        shop.add_field(name=f"__**Iron Pickaxe**__ 128{self.emerald}", value=f"``{ctx.prefix}buy iron pickaxe``", inline=True)
        shop.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        shop.add_field(name=f"__**Gold Pickaxe**__ 512{self.emerald}", value=f"``{ctx.prefix}buy gold pickaxe``", inline=True)
        shop.add_field(name=f"__**Diamond Pickaxe**__ 2048{self.emerald}", value=f"``{ctx.prefix}buy diamond pickaxe``", inline=True)
        shop.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        shop.add_field(name=f"__**Netherite Pickaxe**__ 8192{self.emerald} 4<:netherite_scrap:676974675091521539>", value=f"``{ctx.prefix}buy netherite pickaxe``", inline=True)
        shop.set_footer(text=f"Pickaxes allow you to obtain more emeralds while using the {ctx.prefix}mine command!")
        await ctx.send(embed=shop)

    @shop.command(name="magic")
    async def shop_books(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop [Magic Items]", url=discord.Embed.Empty, icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
        shop.add_field(name=f"__**Fortune I Book**__ 120{self.emerald}", value=f"``{ctx.prefix}buy fortune i book``", inline=True)
        shop.add_field(name=f"__**Haste I Potion**__ 120{self.emerald}", value=f"``{ctx.prefix}buy haste i potion``", inline=True)
        shop.add_field(name=f"__**Lure I Book**__ 120{self.emerald}", value=f"``{ctx.prefix}buy lure i book``", inline=True)
        await ctx.send(embed=shop)

    @shop.command(name="other")
    async def shop_other(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop [Other]", url=discord.Embed.Empty, icon_url="http://olimone.ddns.net/images/villagerbotsplash1.png")
        shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
        shop.add_field(name=f"__**Jar of Bees**__ 8{self.emerald}", value=f"``{ctx.prefix}buy jar of bees``", inline=True)
        shop.add_field(name=f"__**Netherite Scrap**__ (<:netherite_scrap:676974675091521539>) 32{self.emerald}", value=f"``{ctx.prefix}buy netherite scrap``", inline=True)
        shop.add_field(name=f"__**Fishing Rod**__ 64{self.emerald}", value=f"``{ctx.prefix}buy fishing rod``", inline=True)
        await ctx.send(embed=shop)

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx):
        u = ctx.author
        pick = await self.db.get_pickaxe(u.id)
        contents = f"**{pick} pickaxe**\n"

        bal = await self.db.get_balance(ctx.author.id)
        if not bal <= 0:
            s = "s"
            if bal == 1:
                s = ""
            contents += f"{bal} emerald{s}{self.emerald}\n"

        inv = discord.Embed(color=discord.Color.green(), description=contents)

        contents = ""
        i = 0
        rows = 10
        items = await self.db.get_items(u.id)
        for item in items:
            i += 1
            m = await self.db.get_item(u.id, item[0])
            contents += f"{m[1]}x **{m[0]}** ({m[2]}{self.emerald})\n"
            if i % rows == 0:
                if i <= rows:
                    inv.add_field(name="Sellable Items", value=contents, inline=False)
                else:
                    inv.add_field(name="More Sellable Items", value=contents, inline=False)
                contents = ""
        if contents is not "":
            if i <= rows:
                inv.add_field(name="Sellable Items", value=contents, inline=False)
            else:
                inv.add_field(name="More Sellable Items", value=contents, inline=False)

        if not u.avatar_url:
            inv.set_author(name=f"{u.display_name}'s Inventory", url=discord.Embed.Empty)
        else:
            inv.set_author(name=f"{u.display_name}'s Inventory", icon_url=str(u.avatar_url_as(static_format="png")))
        await ctx.send(embed=inv)

    @commands.command(name="vault", aliases=["viewvault"])
    async def view_vault(self, ctx):
        vault = await self.db.get_vault(ctx.author.id)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description=f"{ctx.author.mention}'s vault: {vault[0]}<:emerald_block:679121595150893057>/{vault[1]} ({vault[0]*9}{self.emerald})"))

    @commands.command(name="buy")
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def buy(self, ctx, *, _item: str):
        await ctx.trigger_typing()

        item = _item.lower()

        try: # So proud of this
            amount = int(item.split(" ")[0])
            item = item.replace(f"{amount} ", "")
        except ValueError:
            amount = 1

        if amount > 5000:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't buy more than 5000 of an item at once!"))
            return

        their_bal = await self.db.get_balance(ctx.author.id)

        pickaxes = {"stone pickaxe": [32, "stone"],
                    "iron pickaxe": [128, "iron"],
                    "gold pickaxe": [512, "gold"],
                    "diamond pickaxe": [2048, "diamond"],
                    "netherite pickaxe": [8192, "netherite"]}

        # Items which aren't in shop_items.json
        if pickaxes.get(item) is not None:
            if await self.db.get_pickaxe(ctx.author.id) != item.replace(" pickaxe", ""):
                if their_bal >= pickaxes[item][0]:
                    if item == "netherite pickaxe":
                        scrap = await self.db.get_item(ctx.author.id, "Netherite Scrap")
                        if scrap is not None and scrap[1] >= 4:
                            await self.db.remove_item(ctx.author.id, "Netherite Scrap", 4)
                        else:
                            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough Netherite Scrap! (It can be bought in the Villager Shop)"))
                            return
                    await self.db.set_balance(ctx.author.id, their_bal - pickaxes[item][0])
                    await self.db.set_pickaxe(ctx.author.id, pickaxes[item][1])
                    a = "a"
                    for v in ["a", "e", "i", "o", "u"]:
                        if item.startswith(v):
                            a = "an"
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have purchased {a} **{item}**!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase this item again!"))
            await self.update_user_role(ctx.author.id)
            return

        shop_item = self.g.shop_items.get(item)
        if shop_item is not None:
            their_bal = await self.db.get_balance(ctx.author.id)
            if shop_item[0]*amount <= their_bal:
                db_item = await self.db.get_item(ctx.author.id, shop_item[2][0])
                if db_item is not None:
                    db_item_count = db_item[1]
                else:
                    db_item_count = 0
                if eval(shop_item[1]):
                    await self.db.set_balance(ctx.author.id, their_bal - shop_item[0]*amount)
                    await self.db.add_item(ctx.author.id, shop_item[2][0], amount, shop_item[2][1])
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have bought {amount}x **{db_item[0]}**! (You now have {db_item[1]+amount})"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't buy any more of that item!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You don't have enough emeralds to buy that much! (You need {shop_item[0]*amount}{self.emerald})"))
            return

        # Skream @ user for speling incorectumly.
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not an item you can buy in the Villager Shop!"))

    async def update_user_role(self, user_id):
        guild = self.bot.get_guild(641117791272960031)
        member = guild.get_member(user_id)
        if member is not None:
            pickaxe_type = await self.db.get_pickaxe(user_id)
            if pickaxe_type == "netherite":
                try:
                    await member.add_roles(guild.get_role(697457303477026856))
                    await member.remove_roles(guild.get_role(697457637763186809), guild.get_role(697457970661031957),
                                              guild.get_role(697458756958552114), guild.get_role(697457399295901786))
                except discord.HTTPException:
                    pass
            elif pickaxe_type == "diamond":
                try:
                    await member.add_roles(guild.get_role(697457399295901786))
                    await member.remove_roles(guild.get_role(697457637763186809), guild.get_role(697457970661031957),
                                              guild.get_role(697458756958552114), guild.get_role(697457303477026856))
                except discord.HTTPException:
                    pass
            elif pickaxe_type == "gold":
                try:
                    await member.add_roles(guild.get_role(697458756958552114))
                    await member.remove_roles(guild.get_role(697457637763186809), guild.get_role(697457970661031957),
                                              guild.get_role(697457399295901786), guild.get_role(697457303477026856))
                except discord.HTTPException:
                    pass
            elif pickaxe_type == "iron":
                try:
                    await member.add_roles(guild.get_role(697457970661031957))
                    await member.remove_roles(guild.get_role(697457637763186809), guild.get_role(697458756958552114),
                                              guild.get_role(697457399295901786), guild.get_role(697457303477026856))
                except discord.HTTPException:
                    pass
            elif pickaxe_type == "stone":
                try:
                    await member.add_roles(guild.get_role(697457637763186809))
                    await member.remove_roles(guild.get_role(697457970661031957), guild.get_role(697458756958552114),
                                              guild.get_role(697457399295901786), guild.get_role(697457303477026856))
                except discord.HTTPException:
                    pass
            elif pickaxe_type == "wood":
                try:
                    await member.remove_roles(guild.get_role(697457637763186809), guild.get_role(697457970661031957), guild.get_role(697458756958552114),
                                              guild.get_role(697457399295901786), guild.get_role(697457303477026856))
                except discord.HTTPException:
                    pass


    @commands.command(name="sell")
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def sell_item(self, ctx, *, item: str):
        try:
            amount = int(item.split(" ")[0])
            item = item.replace(f"{amount} ", "")
        except ValueError:
            amount = 1

        _item = await self.db.get_item(ctx.author.id, item)
        if _item is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Either you don't have that item, or that item cannot be sold."))
            return

        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot sell 0 or a negative amount of an item!"))
            return
        if amount > _item[1]:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot sell more than you have of that item!"))
            return
        await self.db.set_balance(ctx.author.id, await self.db.get_balance(ctx.author.id) + _item[2] * amount)
        await self.db.remove_item(ctx.author.id, item, amount)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have sold {amount}x {_item[0]} for {_item[2]*amount}{self.emerald}."))

    @commands.command(name="give")
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    async def give_stuff(self, ctx, rec: discord.User, amount: int, item=None):
        if ctx.author.bot:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Remember, bot's don't have any rights, and as a result can't own items."))
            return
        if item is not None:
            if item.lower() != "emeralds" and item.lower() != "emerald":
                for item in await self.db.get_items(ctx.author.id):
                    if item[0] in ctx.message.content:
                        await self.give_item(ctx, rec, amount, item[0])
                        return
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid item you can give. (You don't own it, or it doesn't exist)"))
                return
        if amount < 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You dumb dumb! You can't give someone negative emeralds!"))
            return
        if amount == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You dumb dumb! You can't give someone 0 emeralds!"))
            return
        if await self.db.get_balance(ctx.author.id) < amount:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds to do that!", "You can't give more than you have!",
                                                                                                "You don't have enough emeralds!"])))
        else:
            await self.db.set_balance(rec.id, await self.db.get_balance(rec.id) + amount)
            await self.db.set_balance(ctx.author.id, await self.db.get_balance(ctx.author.id) - amount)
            if amount == 1:
                plural = ""
            else:
                plural = "s"
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{ctx.author.mention} gave {rec.mention} {amount}{self.emerald}"))

    async def give_item(self, ctx, rec, amount, _item):
        if amount < 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You absolute buffoon! You can't give someone a negative amount of something!"))
            return
        if amount == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You absolute buffoon! You can't give someone zero of something!"))
            return
        item = await self.db.get_item(ctx.author.id, _item)
        if item is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not a valid item you can give. (You don't own it, or it doesn't exist)"))
            return
        if amount > item[1]:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot give more of an item than you own."))
            return
        await self.db.remove_item(ctx.author.id, _item, amount)
        await self.db.add_item(rec.id, item[0], amount, item[2])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{ctx.author.mention} gave {rec.mention} {amount}x {_item}."))

    @commands.command(name="mine", aliases=["mein"])
    @commands.guild_only()
    @commands.cooldown(1, 1.4, commands.BucketType.user) # 1.4
    async def mine(self, ctx):
        if not await self.problem(ctx):
            return
        await self.db.increment_vault_max(ctx.author.id)
        pickaxe = await self.db.get_pickaxe(ctx.author.id)
        if pickaxe == "wood":
            minin = ["dirt", "dirt", "emerald", "dirt", "cobblestone", "cobblestone", "cobblestone", "emerald", "coal", "coal", "cobblestone", "cobblestone", "dirt",
                     "dirt", "iron ore", "cobblestone", "coal", "coal", "coal", "iron ore", "iron ore", "emerald", "dirt", "cobblestone", "dirt", "emerald"] # 4 emeralds
        elif pickaxe == "stone":
            minin = ["dirt", "dirt", "iron ore", "dirt", "emerald", "dirt", "cobblestone", "emerald", "coal", "iron ore", "emerald", "cobblestone", "dirt",
                     "dirt", "iron ore", "cobblestone", "emerald", "coal", "cobblestone", "iron ore", "iron ore", "dirt", "dirt", "cobblestone", "dirt", "emerald"] # 5 emeralds
        elif pickaxe == "iron":
            minin = ["dirt", "dirt", "emerald", "dirt", "cobblestone", "emerald", "cobblestone", "emerald", "coal", "emerald", "cobblestone", "cobblestone", "dirt",
                     "emerald", "iron ore", "cobblestone", "coal", "coal", "lapis lazuli", "iron ore", "emerald", "dirt", "dirt", "cobblestone", "dirt", "emerald"] # 7 emeralds
        elif pickaxe == "gold":
            minin = ["dirt", "emerald", "dirt", "emerald", "cobblestone", "emerald", "cobblestone", "emerald", "coal", "emerald", "diamond", "cobblestone", "dirt",
                     "dirt", "iron ore", "emerald", "gold ore", "coal", "emerald", "iron ore", "iron ore", "cobblestone", "dirt", "lapis lazuli", "dirt", "emerald"] # 8 emeralds
        elif pickaxe == "diamond":
            minin = ["obsidian", "emerald", "dirt", "redstone", "cobblestone", "emerald", "diamond ore", "emerald", "coal", "emerald", "diamond", "cobblestone", "emerald",
                     "emerald", "iron ore", "diamond", "emerald", "redstone", "emerald", "iron ore", "obsidian", "cobblestone", "dirt", "emerald", "obsidian", "emerald"] # 10 emeralds
        elif pickaxe == "netherite":
            minin = ["obsidian", "emerald", "emerald", "redstone", "cobblestone", "emerald", "diamond ore", "emerald", "emerald", "emerald", "diamond", "cobblestone", "emerald",
                     "emerald", "iron ore", "diamond", "emerald", "redstone", "emerald", "iron ore", "obsidian", "emerald", "dirt", "emerald", "obsidian", "emerald"] # 13 emeralds
        found = choice(minin)
        if found == "emerald":
            items = await self.db.get_items(ctx.author.id)
            mult = 1
            choices = [1, 1]
            top = 0
            for item in items:
                if item[0] == "Bane Of Pillagers Amulet": # Amulet should also protecc against pillagers cause yknow bane of pillagers etc...
                    choices = [2, 3, 4, 5, 6]
                    top = 15
                elif item[0] == "Fortune III Book":
                    if 11 > top:
                        choices = [1, 1, 2, 3, 4]
                        top = 11
                elif item[0] == "Fortune II Book":
                    if 8 > top:
                        choices = [1, 1, 1, 2, 3]
                        top = 8
                elif item[0] == "Fortune I Book":
                    if 4 > top:
                        choices = [1, 1, 2]
                        top = 4
                mult = choice(choices)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice([f"You found {mult}{self.emerald}!",
                                                                                                f"You mined up {mult}{self.emerald}!",
                                                                                                f"You got {mult}{self.emerald}!"])))
            await self.db.set_balance(ctx.author.id, await self.db.get_balance(ctx.author.id) + 1 * mult)
        else:
            for c in self.g.items:
                if randint(0, c[2]) == 1:
                    a = "a"
                    for vowel in ["a", "e", "i", "o", "u"]:
                        if c[0].startswith(vowel):
                            a = "an"
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice([
                        f"You {choice(['found', 'got'])} {a} {c[0]} (Worth {c[1]}{self.emerald}) in an abandoned mineshaft!",
                        f"You {choice(['found', 'got'])} {a} {c[0]} (Worth {c[1]}{self.emerald}) in a chest while mining!",
                        f"You {choice(['found', 'got'])} {a} {c[0]} (Worth {c[1]}{self.emerald}) in a chest!",
                        f"You {choice(['found', 'got'])} {a} {c[0]} (Worth {c[1]}{self.emerald}) in a chest near a monster spawner!",
                        f"You {choice(['found', 'got'])} {a} {c[0]} (Worth {c[1]}{self.emerald}) while mining!"])))
                    await self.db.add_item(ctx.author.id, c[0], 1, c[1])
                    return
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You {choice(['found', 'mined', 'mined up', 'found'])} {randint(1, 5)} "
                                                                                        f"{choice(['worthless', 'useless', 'dumb', 'stupid'])} {found}."))

    @mine.error
    async def handle_mine_errors(self, ctx, e): # all errors handler is called after this one, you can set ctx.handled to a boolean
        if isinstance(e, commands.CommandOnCooldown):
            cooldown = e.retry_after
            if await self.db.get_item(ctx.author.id, "Efficiency I Book") is not None:
                cooldown -= .4
            if ctx.author.id in list(self.items_in_use):
                if self.items_in_use[ctx.author.id] == "Haste I Potion":
                    cooldown -= .6
                if self.items_in_use[ctx.author.id] == "Haste II Potion":
                    cooldown -= .9

            if cooldown <= 0:
                await ctx.reinvoke()
            else:
                descs = ["Didn't your parents tell you patience was a virtue? Calm down and wait another {0} seconds.",
                        "Hey, you need to wait another {0} seconds before doing that again.",
                        "Hrmmm, looks like you need to wait another {0} seconds before doing that again.",
                        "Didn't you know patience was a virtue? Wait another {0} seconds."]
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(descs).format(round(cooldown, 2))))

    @commands.command(name="gamble", aliases=["bet"], cooldown_after_parsing=True)
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def gamble(self, ctx, amount: str):
        await self.db.increment_vault_max(ctx.author.id)
        their_bal = await self.db.get_balance(ctx.author.id)
        if str(amount).lower() == "all" or str(amount).lower() == "max":
            amount = their_bal
        else:
            try:
                amount = int(amount)
            except Exception:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Try using an actual number, idiot!"))
                return
        if amount > their_bal:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds!", "You don't have enough emeralds to do that!"])))
            return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You need to gamble with at least 1 emerald!", "You need 1 or more emeralds to gamble with."])))
            return
        roll = randint(1, 6)+randint(1, 6)
        bot_roll = randint(1, 6)+randint(1, 6)
        await asyncio.sleep(.5)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Villager Bot rolled: ``"+str(bot_roll)+"``\nYou rolled: ``"+str(roll)+"``"))
        mult = 1+(randint(10, 30)/100)
        if their_bal < 100:
            mult += 0.2
        rez = ceil(amount*mult)
        if roll > bot_roll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You won {rez-amount}{self.emerald} **|** Multiplier: {int(mult*100)}%"))
            await self.db.set_balance(ctx.author.id, their_bal + (rez - amount))
        elif roll < bot_roll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You lost! Villager Bot won {amount}{self.emerald} from you."))
            await self.db.set_balance(ctx.author.id, their_bal - amount)
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="TIE! No one wins, but maybe Villager Bot will keep your emeralds anyway..."))

    @commands.command(name="pillage", aliases=["steal"], cooldown_after_parsing=True)
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def pillage(self, ctx, victim: discord.User):
        await self.db.increment_vault_max(ctx.author.id)
        if victim.bot:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Bots don't have citizenship and can't own emeralds, go away."))
            ctx.command.reset_cooldown(ctx)
            return
        if ctx.guild.get_member(victim.id) is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't pillage people from other servers!"))
            ctx.command.reset_cooldown(ctx)
            return
        if ctx.author.id == victim.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=victim.display_name + " " + choice(["threw their items into a lava pool.",
                                                                                                                      "commited dig straight down",
                                                                                                                      "suicided via creeper"])))
            ctx.command.reset_cooldown(ctx)
            return
        their_bal = await self.db.get_balance(ctx.author.id)
        if their_bal < 64:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You need 64 emeralds in order to pillage others!"))
            return
        victim_bal = await self.db.get_balance(victim.id)
        if victim_bal < 64:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="It's not worth it, they don't even have 64 emeralds yet."))
            return
        attackers_bees = await self.db.get_item(ctx.author.id, "Jar Of Bees")
        if attackers_bees is None:
            attackers_bees = 0
        else:
            attackers_bees = attackers_bees[1]
        victims_bees = await self.db.get_item(victim.id, "Jar Of Bees")
        if victims_bees is None:
            victims_bees = 0
        else:
            victims_bees = victims_bees[1]
        if attackers_bees > victims_bees:
            heist_success = choice([False, True, True, True, False, True, False, True]) # 5/8
        elif victims_bees > attackers_bees:
            heist_success = choice([False, True, False, False, False, True, False, True]) # 3/8
        else:
            heist_success = choice([False, True]) # 1/2
        if await self.db.get_item(victim.id, "Bane Of Pillagers Amulet") is not None:
            heist_success = choice([False, False, False, False, False, True]) # 1/6
        if heist_success:
            s_amount = ceil(victim_bal*(randint(10, 40)/100))
            await self.db.set_balance(victim.id, victim_bal - s_amount)
            await self.db.set_balance(ctx.author.id, their_bal + s_amount)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice([f"You escaped with {s_amount} {self.emerald}",
                                                                                                f"You got away with {s_amount} {self.emerald}"])))
            await victim.send(embed=discord.Embed(color=discord.Color.green(), description=choice([f"{ctx.author.display_name} stole {s_amount}{self.emerald} from you!",
                                                                                                   f"{ctx.author.display_name} pillaged {s_amount}{self.emerald} from you!",
                                                                                                   f"{ctx.author.display_name} pillaged you and got {s_amount}{self.emerald} from you!."])))
            await self.db.update_pillagerboard(ctx.author.id, s_amount)
        else:
            await self.db.set_balance(victim.id, victim_bal + 32)
            await self.db.set_balance(ctx.author.id, their_bal - 32)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You were caught and paid 32 {self.emerald}"))
            await victim.send(embed=discord.Embed(color=discord.Color.green(), description=choice([f"{ctx.author.display_name} absolutely failed at pillaging you.",
                                                                                                   f"{ctx.author.display_name} got absolutely destroyed pillaging you.",
                                                                                                   f"{ctx.author.display_name} tried to pillage you with their wooden sword."])))

    @commands.group(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def leaderboard(self, ctx):
        await self.db.increment_vault_max(ctx.author.id)
        if ctx.invoked_subcommand is None:
            ctx.command.reset_cooldown(ctx)
            embed = discord.Embed(color=discord.Color.green(), title="__**Villager Bot Leaderboards**__")
            embed.add_field(name="**Emeralds**", value=f"``{ctx.prefix}leaderboard emeralds``", inline=False)
            embed.add_field(name="**Commands Usage**", value=f"``{ctx.prefix}leaderboard commands``", inline=False)
            embed.add_field(name="**Jars Of Bees**", value=f"``{ctx.prefix}leaderboard bees``", inline=False)
            embed.add_field(name="**Emeralds Pillaged**", value=f"``{ctx.prefix}leaderboard pillages``", inline=False)
            await ctx.send(embed=embed)

    @leaderboard.command(name="emeralds", aliases=["money", "em", "ems"])
    async def emerald_leaderboard(self, ctx):
        dbs = await self.bot.db.fetch("SELECT * FROM currency") # Returns list of tuples
        lb = sorted(dbs, key=lambda tup: int(tup[1]), reverse=True) # Sort list
        # Find the rank of the user
        place = -1
        for i in range(0, len(lb), 1):
            if lb[i][0] == ctx.author.id:
                place = i+1
                break
        # Shorten list
        lb = lb[:10]
        if place >= 10:
            lb = lb[:9]
        lb_text = ""
        rank = 1
        for entry in lb:
            user = self.bot.get_user(int(entry[0]))
            if user is None:
                user = "Deleted User     "
            lb_text += f"``{rank}.`` **{entry[1]}{self.emerald}** {str(user)[:-5]} \n"
            rank += 1
        if place >= 10:
            lb_text += "⋮\n"+f"``{place}.`` **{await self.db.get_balance(ctx.author.id)}{self.emerald}** {str(ctx.author)[:-5]}"
        embed = discord.Embed(color=discord.Color.green(), title=f"{self.emerald}__**Emerald Leaderboard**__{self.emerald}", description=lb_text)
        await ctx.send(embed=embed)

    @leaderboard.command(name="commands", aliases=["cmds"])
    async def commands_leaderboard(self, ctx):
        all = self.g.command_leaderboard.items()
        _sorted = sorted(all, reverse=True, key=lambda entry: entry[1])
        # Find the rank of the user
        place = -1
        for i in range(0, len(_sorted), 1):
            if _sorted[i][0] == ctx.author.id:
                place = i+1
                break
        _sorted = _sorted[:10]
        if place >= 10:
            _sorted = _sorted[:9]
        lb_text = ""
        rank = 1
        for entry in _sorted:
            ussr = self.bot.get_user(int(entry[0]))
            if ussr is None:
                ussr = "Unknown User     "
            lb_text += f"``{rank}.`` **{entry[1]} Commands** {str(ussr)[:-5]} \n"
            rank += 1
        if place >= 10:
            lb_text += "⋮\n"+f"``{place}.`` **{self.g.command_leaderboard[ctx.author.id]} Commands** {str(ctx.author)[:-5]}"
        embed = discord.Embed(color=discord.Color.green(), title=f"__**Command Usage Leaderboard**__", description=lb_text)
        await ctx.send(embed=embed)

    @leaderboard.command(name="bees", aliases=["beeboard", "bs"])
    async def beeeeees_leaderboard(self, ctx):
        all_items = await self.db.db.fetch("SELECT id, item, num FROM items")
        all_bees = []
        # Put bees in list of tuples
        for item in all_items:
            if item[1] == "Jar Of Bees":
                all_bees.append([item[0], item[2]])
        _sorted = sorted(all_bees, reverse=True, key=lambda entry: entry[1])
        # Find rank of the user
        place = -1
        for i in range(0, len(_sorted), 1):
            if _sorted[i][0] == ctx.author.id:
                place = i+1
                break
        _sorted = _sorted[:10]
        if place >= 10:
            _sorted = _sorted[:9]
        lb_text = ""
        rank = 1
        for entry in _sorted:
            ussr = self.bot.get_user(int(entry[0]))
            if ussr is None:
                ussr = "Unknown User     "
            lb_text += f"``{rank}.`` **{entry[1]}<:beee:682059180391268352>** {str(ussr)[:-5]} \n"
            rank += 1
        if place >= 10:
            lb_text += "⋮\n"+f"``{place}.`` **{(await self.db.get_item(ctx.author.id, 'Jar Of Bees'))[1]}<:beee:682059180391268352>** {str(ctx.author)[:-5]}"
        embed = discord.Embed(color=discord.Color.green(), title=f"<a:bee:682057109046951956> __**Bee Leaderboard**__ <a:bee:682057109046951956>", description=lb_text)
        await ctx.send(embed=embed)

    @leaderboard.command(name="pillages", aliases=["pil"])
    async def pillager_leaderboard(self, ctx):
        pillagers = await self.db.get_pillagerboard()
        _sorted = sorted(pillagers, reverse=True, key=lambda entry: entry[1]) # Sort by second value in the thingy
        try:
            place = _sorted.index(await self.db.get_pillager(ctx.author.id))+1
        except ValueError:
            place = len(_sorted)+1
        _sorted = _sorted[:10]
        if place >= 10:
            _sorted = _sorted[:9]
        lb_text = ""
        rank = 1
        for entry in _sorted:
            ussr = self.bot.get_user(int(entry[0]))
            if ussr is None:
                ussr = "Unknown User     "
            lb_text += f"``{rank}.`` **{entry[1]}{self.emerald} Stolen** {str(ussr)[:-5]} \n"
            rank += 1
        if place >= 10:
            lb_text += "⋮\n"+f"``{place}.`` **{(await self.db.get_pillager(ctx.author.id))[1]}{self.emerald} Stolen** {str(ctx.author)[:-5]}"
        embed = discord.Embed(color=discord.Color.green(), title=f"{self.emerald} __**Emeralds Pillaged Leaderboard**__ {self.emerald}", description=lb_text)
        await ctx.send(embed=embed)

    @commands.command(name="chug", aliases=["drink"])
    async def use_potion(self, ctx, *, item: str):
        await self.db.increment_vault_max(ctx.author.id)
        if self.items_in_use.get(ctx.author.id) is not None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Currently, you can not use more than one potion at a time."))
            return

        _item = await self.db.get_item(ctx.author.id, item)
        if _item is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Either that potion doesn't exist, or you don't have it!"))
            return

        if item.lower() == "haste i potion":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have chugged a **{_item[0]}** *(which lasts 6 minutes)*!"))
            self.items_in_use[ctx.author.id] = item
            await self.db.remove_item(ctx.author.id, item, 1)
            await asyncio.sleep(60*6)
            self.items_in_use.pop(ctx.author.id)
            await ctx.author.send(embed=discord.Embed(color=discord.Color.green(), description=f"The **{_item[0]}** you chugged earlier has worn off."))
            return

        if item.lower() == "haste ii potion":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have chugged a **{_item[0]}** *(which lasts 4.5 minutes)*!"))
            self.items_in_use[ctx.author.id] = item
            await self.db.remove_item(ctx.author.id, item, 1)
            await asyncio.sleep(60*4.5)
            self.items_in_use.pop(ctx.author.id)
            await ctx.author.send(embed=discord.Embed(color=discord.Color.green(), description=f"The **{_item[0]}** you chugged earlier has worn off."))
            return

        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That's not a potion or it doesn't exist."))

    @commands.command(name="fish")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def fish(self, ctx):
        if not ctx.author.id in [536986067140608041, 418707912836382721]:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="This command is currently disabled due to a exploit found."))
            return
        if not await self.problem(ctx):
            return
        await self.db.increment_vault_max(ctx.author.id)
        bad_catches = ["a rusty nail", "an old shoe", "a broken bottle", "a tin can", "a soda bottle", "a piece of plastic", "a moldy chicken nugget", "a discarded birthday cake",
                       "an old picture frame", "a clump of hair", "some bones", "a forgotten flip flop", "a piece of driftwood", "a kfc container", "a plastic pail", "an old bottle",
                       "a used memory card", "an interesting sea shell", "a bit of sea shell", "a sea dollar", "a dead fish", "a ruined book"]
        good_catches = [("a cod <:cod:701589959458684978>", 3), ("a salmon <:salmon:701589974646128690>", 4),
                        ("a pufferfish <:pufferfish:701590021525733438>", 5), ("a tropical fish <:tropical_fish:701590997808709692>", 10),
                        ("an emerald fish <:emerald_fish:703040458464428112>", 25), ("a diamond fish <:diamond_fish:703041846640640080>", 0)]
        rod = await self.db.get_item(ctx.author.id, "Fishing Rod")
        if rod is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't fish without a fishing rod! (You can buy a wooden one in the shop!)"))
            ctx.command.reset_cooldown(ctx)
        else:
            good_catch_chance = [True, False, False]
            if await self.db.get_item(ctx.author.id, "Luck Of The Sea Book") is not None:
                if choice([False, False, False, True]):
                    for c in self.g.items:
                        if randint(0, c[2]) == 1:
                            a = "a"
                            for vowel in ["a", "e", "i", "o", "u"]:
                                if c[0].startswith(vowel):
                                    a = "an"
                            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice([
                                f"You {choice(['fished up', 'caught'])} {a} {c[0]}! (Worth {c[1]}{self.emerald})",
                                f"You {choice(['fished up', 'caught'])} {a} {c[0]}! (Worth {c[1]}{self.emerald})"])))
                            await self.db.add_item(ctx.author.id, c[0], 1, c[1])
                            return
                good_catch_chance = [True, False]
            if choice(good_catch_chance):
                catch = choice(good_catches)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You {choice(['caught', 'fished up', 'reeled in'])} {catch[0]}! (And sold it for {catch[1]}{self.emerald})"))
                await self.db.set_balance(ctx.author.id, (await self.db.get_balance(ctx.author.id))+catch[1])
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You {choice(['caught', 'fished up', 'reeled in'])} {choice(bad_catches)}..."))

    @fish.error
    async def handle_fish_errors(self, ctx, e): # all errors handler is called after this one, you can set ctx.handled to a boolean
        if isinstance(e, commands.CommandOnCooldown):
            cooldown = e.retry_after
            if await self.db.get_item(ctx.author.id, "Luck Of The Sea Book") is not None:
                cooldown -= 1.5
            if await self.db.get_item(ctx.author.id, "Lure I Book") is not None:
                cooldown -= 4.5

            if cooldown <= 0:
                await ctx.reinvoke()
            else:
                descs = ["Didn't your parents tell you patience was a virtue? Calm down and wait another {0} seconds.",
                        "Hey, you need to wait another {0} seconds before doing that again.",
                        "Hrmmm, looks like you need to wait another {0} seconds before doing that again.",
                        "Didn't you know patience was a virtue? Wait another {0} seconds."]
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(descs).format(round(cooldown, 2))))

    @commands.command(name="harvesthoney", aliases=["honey", "sellhoney"])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def harvest_honey(self, ctx):
        for i in range(0, 3, 1):
            await self.db.increment_vault_max(ctx.author.id)
        bees = await self.db.get_item(ctx.author.id, "Jar Of Bees")
        if bees is not None:
            bees = bees[1]
        else:
            bees = 0
        if bees > 2048:
            bees = 2048
        if bees < 100:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough bees to make this business option viable."))
            ctx.command.reset_cooldown(ctx)
            return
        if choice([True, True, True, False]): # 3/4 chance of getting honey
            jars = bees - randint(ceil(bees/6), ceil(bees/2))
            await self.db.add_item(ctx.author.id, "Honey Jar", jars, 1)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"Apparently bees produce honey and you just collected {jars} jars of it."))
        else:
            bees_lost = randint(ceil(bees/75), ceil(bees/50))
            await self.db.remove_item(ctx.author.id, "Jar Of Bees", bees_lost)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"So apparently bees get mad when you try to steal their honey, who knew... You lost {bees_lost*3} to suicide..."))

    @harvest_honey.error
    async def handle_honey_errors(self, ctx, e):
        if isinstance(e, commands.CommandOnCooldown):
            hours = int(e.retry_after / 3600)
            minutes = int(e.retry_after / 60) % 60
            descs = [f"Didn't your parents tell you patience was a virtue? Calm down and wait another {hours} hour(s) & {minutes} minute(s).",
                     f"Hey, you need to wait another {hours} hour(s) & {minutes} minute(s) before doing that again.",
                     f"Hrmmm, looks like you need to wait another {hours} hour(s) & {minutes} minute(s) before doing that again.",
                     f"Didn't you know patience was a virtue? Wait another {hours} hour(s) & {minutes} minute(s)."]
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(descs)))

def setup(bot):
    bot.add_cog(Econ(bot))
