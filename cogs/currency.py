from discord.ext import commands, tasks
import discord
import json
import asyncio
from random import choice, randint
from math import ceil
import dbl
import psycopg2

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("keys.json", "r") as k:
            keys = json.load(k)
        self.token = keys["dblpy"]
        self.dblpy = dbl.DBLClient(self.bot, self.token, webhook_path="/dblwebhook", webhook_auth=keys["dblpy2"], webhook_port=5000)
        with open("keys.json", "r") as pp:
            self.db = psycopg2.connect(host="localhost",database="villagerbot", user="pi", password=json.load(pp)["postgres"])
        self.save.start()
        
    def cog_unload(self):
        self.save.cancel()
        
    @tasks.loop(seconds=120)
    async def save(self):
        self.db.commit()
        
    async def getb(self, uid):
        cur = self.db.cursor()
        cur.execute("SELECT amount FROM currency WHERE currency.id='"+str(uid)+"'")
        amount = cur.fetchone()
        if str(type(amount)) == "<class 'NoneType'>" or str(type(amount)) == "NoneType":
            cur.execute("INSERT INTO currency VALUES ('"+str(uid)+"', '0')")
            self.db.commit()
            amount = ('0',)
        return int(amount[0])

    async def setb(self, uid, amount):
        await self.getb(uid)
        cur = self.db.cursor()
        cur.execute("UPDATE currency SET amount='"+str(amount)+"' WHERE id='"+str(uid)+"'")
        self.db.commit()
        
    async def getpick(self, uid):
        cur = self.db.cursor()
        cur.execute("SELECT pickaxe FROM pickaxes WHERE pickaxes.id='"+str(uid)+"'")
        pickaxe = cur.fetchone()
        if pickaxe == None:
            cur.execute("INSERT INTO pickaxes VALUES ('"+str(uid)+"', 'wood')")
            self.db.commit()
            pickaxe = ('wood',)
        return str(pickaxe[0])
    
    async def setpick(self, uid, pickaxe):
        await self.getpick(uid)
        cur = self.db.cursor()
        cur.execute("UPDATE pickaxes SET pickaxe='"+str(pickaxe)+"' WHERE id='"+str(uid)+"'")
        self.db.commit()
        
    @commands.command(name="bal", aliases=["balance"])
    async def balance(self, ctx):
        msg = ctx.message.content.replace("!!balance ", "").replace("!!balance", "").replace("!!bal ", "").replace("!!bal", "")
        user = ctx.author
        if msg != "":
            userConvert = commands.UserConverter()
            try:
                user = await commands.UserConverter().convert(ctx, msg)
            except Exception:
                pass
        amount = await self.getb(user.id)
        if amount == 1:
            emerald = "emerald"
        else:
            emerald = "emeralds"
        balEmbed = discord.Embed(color=discord.Color.green(), description=user.mention+" has a total of "+str(amount)+" <:emerald:653729877698150405>")
        await ctx.send(embed=balEmbed)
            
    @commands.command(name="setbal")
    @commands.is_owner()
    async def balset(self, ctx, user: discord.User, amount: int):
        await self.setb(user.id, amount)
        
    @commands.command(name="shop")
    async def shop(self, ctx):
        msg = ctx.message.clean_content.replace("!!shop ", "").replace("!!shop", "")
        shop = discord.Embed(color=discord.Color.green())
        shop.set_author(name="Villager Shop", url=discord.Embed.Empty, icon_url="http://172.10.17.177/images/villagerbotsplash1.png")
        shop.set_footer(text="!!inventory to see what you have!")
        if msg == "":
            shop.add_field(name="__**Pickaxes**__", value="``!!shop pickaxes``")
            await ctx.send(embed=shop)
            return
        if msg == "pickaxes":
            shop.add_field(name="__**Stone Pickaxe**__ 32<:emerald:653729877698150405>", value="``!!buy stone pickaxe``", inline=True)
            shop.add_field(name="__**Iron Pickaxe**__ 128<:emerald:653729877698150405>", value="``!!buy iron pickaxe``", inline=True)
            shop.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            shop.add_field(name="__**Gold Pickaxe**__ 512<:emerald:653729877698150405>", value="``!!buy gold pickaxe``", inline=True)
            shop.add_field(name="__**Diamond Pickaxe**__ 2048<:emerald:653729877698150405>", value="``!!buy diamond pickaxe``", inline=True)
            shop.add_field(name="\uFEFF", value="\uFEFF", inline=True)
            shop.set_footer(text="Pickaxes allow you to get more emeralds while using the !!mine command!")
            await ctx.send(embed=shop)
            return
        
    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx):
        inv = discord.Embed(color=discord.Color.green(), description=str(await self.getb(ctx.author.id))+"x emerald(s)\n1x "+await self.getpick(ctx.author.id)+" pickaxe\n")
        inv.set_author(name=ctx.author.display_name+"'s Inventory", url=discord.Embed.Empty)
        await ctx.send(embed=inv)
        
    @commands.command(name="buy")
    async def buy(self, ctx, *, item):
        if item == "stone pickaxe":
            if await self.getb(ctx.author.id) >= 32:
                if await self.getpick(ctx.author.id) != "stone":
                    await self.setb(ctx.author.id, await self.getb(ctx.author.id)-32)
                    await self.setpick(ctx.author.id, "stone")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a stone pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return
            
        if item == "iron pickaxe":
            if await self.getb(ctx.author.id) >= 128:
                if await self.getpick(ctx.author.id) != "iron":
                    await self.setb(ctx.author.id, await self.getb(ctx.author.id)-128)
                    await self.setpick(ctx.author.id, "iron")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased an iron pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return
            
        if item == "gold pickaxe":
            if await self.getb(ctx.author.id) >= 512:
                if await self.getpick(ctx.author.id) != "gold":
                    await self.setb(ctx.author.id, await self.getb(ctx.author.id)-512)
                    await self.setpick(ctx.author.id, "gold")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a gold pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
            else:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You don't have enough emeralds for this item!"))
            return
            
        if item == "diamond pickaxe":
            if await self.getb(ctx.author.id) >= 2048:
                if await self.getpick(ctx.author.id) != "diamond":
                    await self.setb(ctx.author.id, await self.getb(ctx.author.id)-2048)
                    await self.setpick(ctx.author.id, "diamond")
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You have purchased a diamond pickaxe!"))
                else:
                    await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You can't purchase a pickaxe you already have!"))
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
        if await self.getb(ctx.author.id) < amount:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds to do that!", "You can't give more than you have!", "You don't have enough emeralds!"])))
        else:
            await self.setb(rec.id, await self.getb(rec.id)+amount)
            await self.setb(ctx.author.id, await self.getb(ctx.author.id)-amount)
            if amount == 1:
                plural = ""
            else:
                plural = "s"
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(ctx.author.mention)+" gave "+str(rec.mention)+" "+str(amount)+" emerald"+plural+"."))
            
    @commands.command(name="mine")
    @commands.cooldown(1, 1.5, commands.BucketType.user)
    async def mine(self, ctx):
        pickaxe = await self.getpick(ctx.author.id)
        if pickaxe == "wood":
            minin = ["dirt", "dirt", "emerald", "dirt", "cobblestone", "cobblestone", "cobblestone", "emerald", "coal", "coal", "cobblestone", "cobblestone", "dirt",
                     "dirt", "iron ore", "cobblestone", "coal", "coal", "coal", "iron ore", "iron ore", "emerald", "dirt", "cobblestone", "dirt", "emerald"]
        elif pickaxe == "stone":
            minin = ["dirt", "dirt", "iron ore", "dirt", "emerald", "emerald", "cobblestone", "emerald", "coal", "iron ore", "emerald", "cobblestone", "dirt",
                     "dirt", "iron ore", "cobblestone", "emerald", "coal", "cobblestone", "iron ore", "iron ore", "dirt", "dirt", "cobblestone", "dirt", "emerald"]
        elif pickaxe == "iron":
            minin = ["dirt", "dirt", "emerald", "dirt", "cobblestone", "emerald", "cobblestone", "emerald", "coal", "emerald", "cobblestone", "cobblestone", "dirt",
                     "emerald", "iron ore", "cobblestone", "coal", "coal", "lapis lazuli", "iron ore", "emerald", "dirt", "dirt", "cobblestone", "dirt", "emerald"]
        elif pickaxe == "gold":
            minin = ["dirt", "emerald", "dirt", "emerald", "cobblestone", "emerald", "cobblestone", "emerald", "coal", "emerald", "diamond", "cobblestone", "dirt",
                     "dirt", "iron ore", "emerald", "gold ore", "coal", "emerald", "iron ore", "iron ore", "cobblestone", "dirt", "lapis lazuli", "dirt", "emerald"]
        elif pickaxe == "diamond":
            minin = ["obsidian", "emerald", "dirt", "redstone", "cobblestone", "emerald", "emerald", "emerald", "coal", "emerald", "diamond", "cobblestone", "emerald",
                     "emerald", "iron ore", "diamond", "emerald", "redstone", "emerald", "iron ore", "obsidian", "cobblestone", "dirt", "emerald", "obsidian", "emerald"]
        found = choice(minin)
        if found == "emerald":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["**<:emerald:653729877698150405>** added to your inventory!", "You found an **<:emerald:653729877698150405>**, it's been added to your inventory!",
                                   "You mined up an **<:emerald:653729877698150405>**!", "You found an **<:emerald:653729877698150405>**"])))
            await self.setb(ctx.author.id, await self.getb(ctx.author.id)+1)
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You "+choice(["found", "mined", "mined up", "mined up", "found"])+" "+str(randint(1, 8))+" "+choice(["worthless", "useless", "dumb", "stupid"])+" "+found+"."))
    
    @commands.command(name="gamble", aliases=["bet"], cooldown_after_parsing=True)
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def gamble(self, ctx, amount: str):
        theirbal = await self.getb(ctx.author.id)
        if str(amount).lower() == "all" or str(amount).lower() == "max":
            amount = theirbal
        else:
            try:
                amount = int(amount)
            except Exception:
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Try using an actual number, idiot!"))
                return
        if amount > theirbal:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds!", "You don't have enough emeralds to do that!"])))
            return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You need to gamble with at least 1 emerald!", "You need 1 or more emeralds to gamble with."])))
            return
        roll = randint(1, 6)+randint(1, 6)
        botRoll = randint(1, 6)+randint(1, 6)
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Villager Bot rolled: ``"+str(botRoll)+"``\nYou rolled: ``"+str(roll)+"``"))
        mult = 1+(randint(10, 30)/100)
        if theirbal < 100:
            mult += 0.2
        rez = ceil(amount*mult)
        if roll > botRoll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You won "+str(rez-amount)+" <:emerald:653729877698150405> **|** Multiplier: "+str(int(mult*100))+"%"))
            await self.setb(ctx.author.id, await self.getb(ctx.author.id)+(rez-amount))
        elif roll < botRoll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You lost! Villager Bot won "+str(amount)+" <:emerald:653729877698150405> from you."))
            await self.setb(ctx.author.id, await self.getb(ctx.author.id)-amount)
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="TIE! Maybe Villager Bot will just keep your emeralds anyway..."))
        
    @commands.command(name="pillage", aliases=["steal"], cooldown_after_parsing=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def pillage(self, ctx, user: discord.User):
        if ctx.author.id == user.id:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=user.display_name+" "+choice(["threw their items into a lava pool."])))
            return
        if await self.getb(ctx.author.id) < 64:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You need 64 emeralds in order to pillage others!"))
            return
        if await self.getb(user.id) < 64:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="It's not worth it, they don't even have 64 emeralds yet."))
            return
        heistSuccess = choice([False, True, False, True, False, True])
        if heistSuccess:
            sAmount = ceil(await self.getb(user.id)*(randint(10, 40)/100))
            await self.setb(user.id, await self.getb(user.id)-sAmount)
            await self.setb(ctx.author.id, await self.getb(ctx.author.id)+sAmount)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You escaped with {0} <:emerald:653729877698150405>", "You got away with {0} <:emerald:653729877698150405>"]).format(str(sAmount))))
        else:
            await self.setb(user.id, await self.getb(user.id)+32)
            await self.setb(ctx.author.id, await self.getb(ctx.author.id)-32)
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You were caught and paid 32 <:emerald:653729877698150405>"))
            
    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print(u"\u001b[32mPERSON VOTED ON TOP.GG\u001b[0m")
        userID = int(data["user"])
        multi = 1
        if await self.dblpy.get_weekend_status():
            multi = 2
        await self.setb(userID, await self.getb(userID)+(32*multi))
        user = self.bot.get_user(userID)
        await user.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You have been awarded {0} <:emerald:653729877698150405> for voting for Villager Bot!",
                                                                                                  "You have recieved {0} <:emerald:653729877698150405> for voting for Villager Bot!"]).format(32*multi)))
    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        print(u"\u001b[35mDBL WEBHOOK TEST\u001b[0m")
        channel = self.bot.get_channel(643648150778675202)
        await channel.send(embed=discord.Embed(color=discord.Color.green(), description="DBL WEBHOOK TEST"))
        
def setup(bot):
    bot.add_cog(Currency(bot))