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
        
    @tasks.loop(seconds=30)
    async def save(self):
        self.db.commit()
        
    async def getb(self, uid):
        cur = self.db.cursor()
        cur.execute("SELECT amount FROM currency WHERE currency.id='"+str(uid)+"'")
        amount = cur.fetchone()
        if str(type(amount)) == "<class 'NoneType'>" or str(type(amount)) == "NoneType":
            cur.execute("INSERT INTO currency VALUES ('"+str(uid)+"', '0')")
            amount = ('0',)
        return int(amount[0])

        
    async def setb(self, uid, amount):
        await self.getb(uid)
        cur = self.db.cursor()
        cur.execute("UPDATE currency SET amount='"+str(amount)+"' WHERE id='"+str(uid)+"'")
        
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
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(ctx.author.mention)+" gave "+str(rec.mention)+" "+str(amount)+" emeralds."))
            
    @commands.command(name="mine")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def mine(self, ctx):
        if await self.getb(ctx.author.id) < 64:
            minin = ["dirt", "diamonds", "dirt", "dirt", "cobblestone", "cobblestone", "cobblestone", "emerald", "coal", "coal", "cobblestone", "emerald", "dirt",
                     "emerald", "dirt", "emerald", "coal", "diamonds", "emerald", "iron ore", "iron ore", "emerald", "dirt", "cobblestone", "dirt", "emerald"]
        else:
            minin = ["dirt", "diamonds", "dirt", "dirt", "cobblestone", "cobblestone", "cobblestone", "emerald", "coal", "coal", "cobblestone", "cobblestone", "dirt",
                     "dirt", "dirt", "cobblestone", "coal", "diamonds", "emerald", "iron ore", "iron ore", "emerald", "dirt", "cobblestone", "dirt", "emerald"]
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
        multi = 2
        if await self.dblpy.get_weekend_status():
            multi = 3
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