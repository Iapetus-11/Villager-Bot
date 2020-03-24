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
        self.whoismining = {}

    async def probGen(self):
        x = randint(0, 25)
        y = randint(0, 25)
        return [f"{str(x)}+{str(y)}", str(x+y)]

    @commands.command(name="bal", aliases=["balance"])
    async def balance(self, ctx):
        msg = ctx.message.content.lower().replace(ctx.prefix+"balance ", "").replace(ctx.prefix+"bal ", "")
        try:
            user = await commands.UserConverter().convert(ctx, msg)
        except Exception:
            user = ctx.author
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=user.mention+" has "+str(await self.db.getBal(user.id))+"<:emerald:653729877698150405>"))

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount: str):  # In blocks
        theirbal = await self.db.getBal(ctx.author.id)
        if theirbal < 9:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to deposit!"))
            return
        vault = await self.db.getVault(ctx.author.id)
        if amount.lower() == "all" or amount.lower() == "max":
            amount = vault[1]-vault[0]
            if floor(theirbal/9) < amount:
                amount = floor(theirbal/9)
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
        if amount*9 > theirbal:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't deposit more emeralds than you have!"))
            return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have to deposit one or more emerald blocks at once!"))
            return

        await self.db.setBal(ctx.author.id, theirbal-(9*amount))
        await self.db.setVault(ctx.author.id, vault[0]+amount, vault[1])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have deposited "+str(amount)+" emerald blocks into the vault. ("+str(amount*9)+"<:emerald:653729877698150405>)"))

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount: str): # In emerald blocks
        vault = await self.db.getVault(ctx.author.id)
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

        await self.db.setBal(ctx.author.id, await self.db.getBal(ctx.author.id)+(9*amount))
        await self.db.setVault(ctx.author.id, vault[0]-amount, vault[1])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have withdrawn "+str(amount)+" emerald blocks from the vault. ("+str(amount*9)+"<:emerald:653729877698150405>)"))

    @commands.group(name="shop")
    async def shop(self, ctx):
        if ctx.invoked_subcommand is None:
            shop = discord.Embed(color=discord.Color.green())
            shop.set_author(name="Villager Shop", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
            shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
            shop.add_field(name="__**Pickaxes**__", value="``"+ctx.prefix+"shop pickaxes``")
            shop.add_field(name="__**Other**__", value="``"+ctx.prefix+"shop other``")
            shop.add_field(name="__**Enchanted Books**__", value="``"+ctx.prefix+"shop books``")
            await ctx.send(embed=shop)
    
    @shop.command(name="pickaxes")
    async def shop_pickaxes(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop [Pickaxes]", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
        shop.add_field(name="__**Stone Pickaxe**__ 32<:emerald:653729877698150405>", value="``"+ctx.prefix+"buy stone pickaxe``", inline=True)
        shop.add_field(name="__**Iron Pickaxe**__ 128<:emerald:653729877698150405>", value="``"+ctx.prefix+"buy iron pickaxe``", inline=True)
        shop.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        shop.add_field(name="__**Gold Pickaxe**__ 512<:emerald:653729877698150405>", value="``"+ctx.prefix+"buy gold pickaxe``", inline=True)
        shop.add_field(name="__**Diamond Pickaxe**__ 2048<:emerald:653729877698150405>", value="``"+ctx.prefix+"buy diamond pickaxe``", inline=True)
        shop.add_field(name="\uFEFF", value="\uFEFF", inline=True)
        shop.add_field(name="__**Netherite Pickaxe**__ 8192<:emerald:653729877698150405> 4<:netherite_scrap:676974675091521539>", value="``"+ctx.prefix+"buy netherite pickaxe``", inline=True)
        shop.set_footer(text="Pickaxes allow you to obtain more emeralds while using the "+ctx.prefix+"mine command!")
        await ctx.send(embed=shop)
        
    @shop.command(name="books")
    async def shop_books(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop [Books]", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        shop.add_field(name="__**Fortune I Book**__ 120<:emerald:653729877698150405>", value="``"+ctx.prefix+"buy fortune i book``", inline=True)
        shop.set_footer(text="Enchantment books give you a chance obtain more emeralds while using the "+ctx.prefix+"mine command!")
        await ctx.send(embed=shop)
    
    @shop.command(name="other")
    async def shop_other(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop [Other]", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
        shop.add_field(name="__**Jar of Bees**__ 8<:emerald:653729877698150405>", value="``"+ctx.prefix+"buy jar of bees``", inline=True)
        shop.add_field(name="__**Netherite Scrap**__ (<:netherite_scrap:676974675091521539>)  __**32<:emerald:653729877698150405>**__", value="``"+ctx.prefix+"buy netherite scrap``", inline=True)
        await ctx.send(embed=shop)

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx):
        pick = await self.db.getPick(ctx.author.id)
        contents = pick+" pickaxe\n"

        bal = await self.db.getBal(ctx.author.id)
        if bal == 1:
            contents += "1x emerald\n"
        else:
            contents += str(bal)+"x emeralds\n"

        beecount = await self.db.getBees(ctx.author.id)
        if beecount > 1:
            contents += str(beecount)+"x jars of bees ("+str(beecount*3)+" bees)\n"
        if beecount == 1:
            contents += str(beecount)+"x jar of bees ("+str(beecount*3)+" bees)\n"

        netheritescrapcount = await self.db.getScrap(ctx.author.id)
        if netheritescrapcount > 1:
            contents += str(netheritescrapcount)+"x chunks of netherite scrap\n"
        if netheritescrapcount == 1:
            contents += str(netheritescrapcount)+"x chunk of netherite scrap\n"

        items = await self.db.getItems(ctx.author.id)
        for item in items:
            contents += f"{item[1]}x {item[0]} (sells for {item[2]}<:emerald:653729877698150405>)\n"

        inv = discord.Embed(color=discord.Color.green(), description=contents)
        inv.set_author(name=ctx.author.display_name+"'s Inventory", url=discord.Embed.Empty)
        await ctx.send(embed=inv)

    @commands.command(name="vault", aliases=["viewvault"])
    async def viewVault(self, ctx):
        vault = await self.db.getVault(ctx.author.id)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description=f"{ctx.author.mention}'s vault: {vault[0]}<:emerald_block:679121595150893057>/{vault[1]} ({vault[0]*9}<:emerald:653729877698150405>)"))

    @commands.command(name="buy")
    async def buy(self, ctx, *, itemm):
        item = itemm.lower()
        theirBal = await self.db.getBal(ctx.author.id)

        if item == "fortune i book" or item == "fortune 1 book":
            if theirBal >= 120:
                await self.db.setBal(ctx.author.id, theirBal-120)
                await self.db.addItem(ctx.author.id, "Fortune I Book", 1, 24)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have bought a Fortune I Book."))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to buy a Fortune I Book."))
            return

        if item == "jar of bees":
            if theirBal >= 8:
                await self.db.setBal(ctx.author.id, theirBal-8)
                await self.db.setBees(ctx.author.id, await self.db.getBees(ctx.author.id)+1)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a jar of be"+choice(["e", "eee", "ee", "eeeee", "eeeeeeeeeeeeeeee", "eeeeeeeeeee"])+"s"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to buy a jar of bees."))
            return

        if item == "netherite scrap":
            if theirBal >= 32:
                await self.db.setBal(ctx.author.id, theirBal-32)
                await self.db.setScrap(ctx.author.id, await self.db.getScrap(ctx.author.id)+1)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have bought a piece of netherite scrap"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to purchase some netherite scrap."))

        if item == "stone pickaxe": # "wood" is default
            if theirBal >= 32:
                if await self.db.getPick(ctx.author.id) != "stone":
                    await self.db.setBal(ctx.author.id, theirBal-32)
                    await self.db.setPick(ctx.author.id, "stone")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a stone pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return

        if item == "iron pickaxe":
            if theirBal >= 128:
                if await self.db.getPick(ctx.author.id) != "iron":
                    await self.db.setBal(ctx.author.id, theirBal-128)
                    await self.db.setPick(ctx.author.id, "iron")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased an iron pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return

        if item == "gold pickaxe":
            if theirBal >= 512:
                if await self.db.getPick(ctx.author.id) != "gold":
                    await self.db.setBal(ctx.author.id, theirBal-512)
                    await self.db.setPick(ctx.author.id, "gold")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a gold pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return

        if item == "diamond pickaxe":
            if theirBal >= 2048:
                if await self.db.getPick(ctx.author.id) != "diamond":
                    await self.db.setBal(ctx.author.id, theirBal-2048)
                    await self.db.setPick(ctx.author.id, "diamond")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a diamond pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return

        if item == "netherite pickaxe":
            if theirBal >= 8192:
                if await self.db.getScrap(ctx.author.id) >= 4:
                    if await self.db.getPick(ctx.author.id) != "netherite":
                        await self.db.setBal(ctx.author.id, theirBal-8192)
                        await self.db.setScrap(ctx.author.id, await self.db.getScrap(ctx.author.id)-4)
                        await self.db.setPick(ctx.author.id, "netherite")
                        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a netherite pickaxe!"))
                    else:
                        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough netherite scrap for this item!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return

        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That is not an item you can buy in the Villager Shop!"))
        
    @commands.command(name="sell")
    async def sellitem(self, ctx, am: str, *, item: str):
        itemm = await self.db.getItem(ctx.author.id, item)
        if am == "all" or am == "max":
            amount = int(itemm[1])
        else:
            try:
                amount = int(am)
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You idiot, try sending an actual number"))
                return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot sell 0 or a negative amount of an item!"))
            return
        if itemm is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Either you don't have that item, or that item cannot be sold."))
            return
        if amount > itemm[1]:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You cannot sell more than you have of that item!"))
            return
        await self.db.setBal(ctx.author.id, await self.db.getBal(ctx.author.id)+itemm[2]*amount)
        await self.db.removeItem(ctx.author.id, item, amount)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"You have sold {amount}x {item} for {itemm[2]*amount}<:emerald:653729877698150405>."))

    @commands.command(name="give", aliases=["donate"])
    async def give(self, ctx, rec: discord.User, amount: int):
        if amount < 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You dumb dumb! You can't give someone negative emeralds!"))
            return
        if amount == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You dumb dumb! You can't give someone 0 emeralds!"))
            return
        if await self.db.getBal(ctx.author.id) < amount:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds to do that!", "You can't give more than you have!",
                                                                                                "You don't have enough emeralds!"])))
        else:
            await self.db.setBal(rec.id, await self.db.getBal(rec.id)+amount)
            await self.db.setBal(ctx.author.id, await self.db.getBal(ctx.author.id)-amount)
            if amount == 1:
                plural = ""
            else:
                plural = "s"
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(ctx.author.mention)+" gave "+str(rec.mention)+" "+str(amount)+" emerald"+plural+"."))

    @commands.command(name="mine")
    @commands.guild_only()
    @commands.cooldown(1, 1.4, commands.BucketType.user)
    async def mine(self, ctx):
        if ctx.author.id in self.whoismining.keys():
            if self.whoismining[ctx.author.id] >= 100:
                prob = await self.probGen()
                await ctx.send("Please solve this problem to continue: ``"+prob[0]+"``")
                msg = await self.bot.wait_for("message")
                while msg.author.id is not ctx.author.id:
                    msg = await self.bot.wait_for("message")
                if msg.clean_content == prob[1]:
                    await ctx.send("Correct answer!")
                    self.whoismining[ctx.author.id] = 0
                else:
                    await ctx.send("Incorrect answer.")
                return
            self.whoismining[ctx.author.id] += 1
        else:
            self.whoismining[ctx.author.id] = 1
        pickaxe = await self.db.getPick(ctx.author.id)
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
            items = await self.db.getItems(ctx.author.id)
            mult = 1
            for item in items:
                if item[0] == "Bane Of Pillagers Amulet": # Amulet should also protecc against pillagers cause yknow bane of pillagers etc...
                    mult = choice([1, 2, 3, 4, 5])
                elif item[0] == "Fortune III Book":
                    mult = choice([1, 1, 2, 3, 4])
                elif item[0] == "Fortune II Book":
                    mult = choice([1, 1, 1, 2, 3])
                elif item[0] == "Fortune I Book":
                    mult = choice([1, 1, 2])
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice([f"You found {mult} <:emerald:653729877698150405>!",
                                                                                                f"You mined up {mult} <:emerald:653729877698150405>!",
                                                                                                f"You got {mult} <:emerald:653729877698150405>!"])))
            await self.db.setBal(ctx.author.id, await self.db.getBal(ctx.author.id)+1*mult)
        else:
            for c in self.g.collectables:
                if randint(0, c[2]) == c[3]:
                    await ctx.send(choice([f"You {choice(['found', 'got'])} a {c[0]} (Worth {c[1]}) in an abandoned mineshaft!",
                                           f"You {choice(['found', 'got'])} a {c[0]} (Worth {c[1]}) in a chest while mining!",
                                           f"You {choice(['found', 'got'])} a {c[0]} (Worth {c[1]}) in a chest!",
                                           f"You {choice(['found', 'got'])} a {c[0]} (Worth {c[1]}) in a chest near a monster spawner!"]))
                    await self.db.addItem(ctx.author.id, c[0], 1, c[1])
                    return
            if randint(0, 999) == 420:
                await self.db.addItem(ctx.author.id, "Fortune II Book", 1, 120)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You found a **Fortune II Book**!! Also, some rare dirt..."))
            elif randint(0, 9999) == 6669:
                await self.db.addItem(ctx.author.id, "Fortune III Book", 1, 420)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You found a **Fortune III Book**!! Also, some rare dirt..."))
            elif randint(0, 99999) == 6969:
                await self.db.addItem(ctx.author.id, "Bane Of Pillagers Amulet", 1, 8192)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have literally just found the rarest fucking thing ever, **The Bane Of Pillagers Amulet**!! Also, some rare dirt..."))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You " + choice(["found", "mined", "mined up", "found"])+" "+str(randint(1, 8)) + " "
                                                   + choice(["worthless", "useless", "dumb", "stupid"])+" "+found+"."))

    @commands.command(name="gamble", aliases=["bet"], cooldown_after_parsing=True)
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def gamble(self, ctx, amount: str):
        theirBal = await self.db.getBal(ctx.author.id)
        if str(amount).lower() == "all" or str(amount).lower() == "max":
            amount = theirBal
        else:
            try:
                amount = int(amount)
            except Exception:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Try using an actual number, idiot!"))
                return
        if amount > theirBal:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds!", "You don't have enough emeralds to do that!"])))
            return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You need to gamble with at least 1 emerald!", "You need 1 or more emeralds to gamble with."])))
            return
        roll = randint(1, 6)+randint(1, 6)
        botRoll = randint(1, 6)+randint(1, 6)
        await asyncio.sleep(.5)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Villager Bot rolled: ``"+str(botRoll)+"``\nYou rolled: ``"+str(roll)+"``"))
        mult = 1+(randint(10, 30)/100)
        if theirBal < 100:
            mult += 0.2
        rez = ceil(amount*mult)
        if roll > botRoll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You won "+str(rez-amount)+" <:emerald:653729877698150405> **|** Multiplier: "+str(int(mult*100))+"%"))
            await self.db.setBal(ctx.author.id, theirBal+(rez-amount))
        elif roll < botRoll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You lost! Villager Bot won "+str(amount)+" <:emerald:653729877698150405> from you."))
            await self.db.setBal(ctx.author.id, theirBal-amount)
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="TIE! No one wins, but maybe Villager Bot will keep your emeralds anyway..."))

    @commands.command(name="pillage", aliases=["steal"], cooldown_after_parsing=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def pillage(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=user.display_name+" "+choice(["threw their items into a lava pool.", "commited dig straight down", "suicided via creeper"])))
            return
        theirBal = await self.db.getBal(ctx.author.id)
        if theirBal < 64:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You need 64 emeralds in order to pillage others!"))
            return
        victimBal = await self.db.getBal(user.id)
        if victimBal < 64:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="It's not worth it, they don't even have 64 emeralds yet."))
            return
        attackersBees = await self.db.getBees(ctx.author.id)
        victimsBees = await self.db.getBees(user.id)
        if attackersBees > victimsBees:
            heistSuccess = choice([False, True, True, True, False, True, False, True])
        elif victimsBees > attackersBees:
            heistSuccess = choice([False, True, False, False, False, True, False, True])
        else:
            heistSuccess = choice([False, True, False, True, False, True, False, True])
        if heistSuccess:
            sAmount = ceil(victimBal*(randint(10, 40)/100))
            await self.db.setBal(user.id, victimBal-sAmount)
            await self.db.setBal(ctx.author.id, theirBal+sAmount)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You escaped with {0} <:emerald:653729877698150405>", "You got away with {0} <:emerald:653729877698150405>"]).format(str(sAmount))))
        else:
            await self.db.setBal(user.id, victimBal+32)
            await self.db.setBal(ctx.author.id, theirBal-32)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You were caught and paid 32 <:emerald:653729877698150405>"))

    @commands.command(name="leaderboard", aliases=["lb"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def leaderboard(self, ctx):
        self.db.db.commit()
        cur = self.db.db.cursor()
        cur.execute("SELECT * FROM currency")
        dbs = cur.fetchall() # Returns list of tuples
        done = []
        lb = sorted(dbs, key=lambda tup: int(tup[1]), reverse=True)[:9]
        lbtext = ""
        for entry in lb:
            user = self.bot.get_user(int(entry[0]))
            if user is None:
                user = "Deleted User     "
            lbtext += f"{entry[1]}<:emerald:653729877698150405> {str(user)[:-5]} \n"
        embed = discord.Embed(color=discord.Color.green(), title="<:emerald:653729877698150405>__**Emerald Leaderboard**__<:emerald:653729877698150405>", description=lbtext)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Econ(bot))
