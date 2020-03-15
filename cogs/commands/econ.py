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
        
    @commands.command(name="bal")
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
        
    @commands.command(name="withdraw")
    async def withdraw(self, ctx, amount: str): #emerald blocks
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
        msg = ctx.message.clean_content.lower().replace(ctx.prefix+"shop ", "").replace(ctx.prefix+"shop", "")
        if msg == "pickaxes":
            await self.shop_pickaxes(ctx)
        elif msg == "other":
            await self.shop_other(ctx)
        else:
            shop = discord.Embed(color=discord.Color.green())
            shop.set_author(name="Villager Shop", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
            shop.set_footer(text=ctx.prefix+"inventory to see what you have!")
            shop.add_field(name="__**Pickaxes**__", value="``"+ctx.prefix+"shop pickaxes``")
            shop.add_field(name="__**Other**__", value="``"+ctx.prefix+"shop other``")
            await ctx.send(embed=shop)
    
    async def shop_pickaxes(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
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
    
    async def shop_other(self, ctx):
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
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
            contents += "1 emerald\n"
        else:
            contents += str(bal)+" emeralds\n"
        
        beecount = await self.db.getBees(ctx.author.id)
        if beecount > 1:
            contents += str(beecount)+" jars of bees ("+str(beecount*3)+" bees)\n"
        if beecount == 1:
            contents += str(beecount)+" jar of bees ("+str(beecount*3)+" bees)\n"
            
        netheritescrapcount = await self.db.getScrap(ctx.author.id)
        if netheritescrapcount > 1:
            contents += str(netheritescrapcount)+" chunks of netherite scrap\n"
        if netheritescrapcount == 1:
            contents += str(netheritescrapcount)+" chunk of netherite scrap\n"
            
        inv = discord.Embed(color=discord.Color.green(), description=contents)
        inv.set_author(name=ctx.author.display_name+"'s Inventory", url=discord.Embed.Empty)
        await ctx.send(embed=inv)
        
    @commands.command(name="vault", aliases=["viewvault"])
    async def viewVault(self, ctx):
        vault = await self.db.getVault(ctx.author.id)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=ctx.author.mention+"'s vault: "+str(vault[0])+"<:emerald_block:679121595150893057>/"+str(vault[1])))
        
    @commands.command(name="buy")
    async def buy(self, ctx, *, itemm):
        item = itemm.lower()
        theirBal = await self.db.getBal(ctx.author.id)
        
        if item == "jar of bees":
            if theirBal >= 8:
                await self.db.setBal(ctx.author.id, theirBal-8)
                await self.db.setBees(ctx.author.id, await self.db.getBees(ctx.author.id)+1)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a jar of be"+choice(["e", "eee", "ee", "eeeee", "eeeeeeeeeeeeeeee", "eeeeeeeeeee"])+"s"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to buy a jar of bees."))
                
        if item == "netherite scrap":
            if theirBal >= 32:
                await self.db.setBal(ctx.author.id, theirBal-32)
                await self.db.setScrap(ctx.author.id, await self.db.getScrap(ctx.author.id)+1)
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have bought a piece of netherite scrap"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds to purchase some netherite scrap."))
        
        if item == "stone pickaxe": #"wood" is default
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
    @commands.cooldown(1, 1.5, commands.BucketType.user)
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
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["**<:emerald:653729877698150405>** added to your inventory!",
                                                                                                "You found an **<:emerald:653729877698150405>**, it's been added to your inventory!",
                                                                                                "You mined up an **<:emerald:653729877698150405>**!",
                                                                                                "You found an **<:emerald:653729877698150405>**"])))
            await self.db.setBal(ctx.author.id, await self.db.getBal(ctx.author.id)+1)
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You "+choice(["found", "mined", "mined up", "mined up", "found"])+" "+str(randint(1, 8))+" "
                                               +choice(["worthless", "useless", "dumb", "stupid"])+" "+found+"."))
            
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
        
def setup(bot):
    bot.add_cog(Econ(bot))