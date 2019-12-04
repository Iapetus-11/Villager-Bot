from discord.ext import commands, tasks
import discord
import json
import asyncio
from random import choice, randint
from math import ceil
import dbl

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = json.load(open("keys.json", "r"))["dblpy"]
        self.dblpy = dbl.DBLClient(self.bot, self.token, webhook_path="/dblwebhook", webhook_auth="YuriFuckingTarded172fuckingPain", webhook_port=5000, autoupdate=True)
        with open("currency.json", "r") as file:
            global inventories
            inventories = json.load(file)
        
    @tasks.loop(seconds=30)
    async def save(self):
        with open("currency.json", "w") as file:
            global inventories
            file.write(json.dumps(inventories))
            
    @commands.command(name="bal", aliases=["balance", "money", "emeralds"])
    async def balance(self, ctx):
        global inventories
        if not str(ctx.message.author.id) in inventories:
            inventories[str(ctx.message.author.id)] = 0
        amount = inventories[str(ctx.message.author.id)]
        if amount == 1:
            emerald = "emerald"
        else:
            emerald = "emeralds"
        balEmbed = discord.Embed(color=discord.Color.green(), description="You have a total of "+str(amount)+" "+emerald+".")
        await ctx.send(embed=balEmbed)
            
    @commands.command(name="give", aliases=["donate"])
    async def give(self, ctx, rec: discord.User, amount: int):
        global inventories
        if not str(rec.id) in inventories:
            inventories[str(rec.id)] = 0
        if not str(ctx.message.author.id) in inventories:
            inventories[str(ctx.message.author.id)] = 0
        if inventories[str(ctx.message.author.id)] < amount:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds to do that!", "You can't give more than you have!", "You don't have enough emeralds!"])))
        else:
            inventories[str(rec.id)] = inventories[str(rec.id)] + amount
            inventories[str(ctx.message.author.id)] = inventories[str(ctx.message.author.id)] - amount
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=str(ctx.message.author.mention)+" gave "+str(rec.mention)+" "+str(amount)+" emeralds."))
            
    @commands.command(name="mine")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def mine(self, ctx):
        global inventories
        if not str(ctx.message.author.id) in inventories:
            inventories[str(ctx.message.author.id)] = 0
        minin = ["dirt", "diamonds", "dirt", "dirt", "cobblestone", "cobblestone", "cobblestone", "emerald", "coal", "coal", "cobblestone", "cobblestone", "dirt",
                 "dirt", "dirt", "cobblestone", "coal", "diamonds", "emerald", "iron ore", "iron", "emerald", "dirt", "cobblestone", "dirt", "emerald"]
        found = choice(minin)
        if found == "emerald":
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["**EMERALD** added to your inventory!", "You found an **EMERALD**, it's been added to your inventory!",
                                   "You mined up an **EMERALD**!", "You found an **EMERALD**"])))
            inventories[str(ctx.message.author.id)] = inventories[str(ctx.message.author.id)] + 1
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You "+choice(["found", "mined", "mined up", "mined up", "found"])+" "+str(randint(1, 8))+" "+choice(["worthless", "useless"])+" "+found+"."))
    
    @commands.command(name="gamble", aliases=["bet"])
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def gamble(self, ctx, amount: int):
        global inventories
        if not str(ctx.message.author.id) in inventories:
            inventories[str(ctx.message.author.id)] = 0
        if amount > inventories[str(ctx.message.author.id)]:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You don't have enough emeralds!", "You don't have enough emeralds to do that!"])))
            return
        if amount < 1:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You need to gamble with at least 1 emerald!", "You need 1 or more emeralds to gamble with."])))
            return
        roll = randint(1, 6)+randint(1, 6)
        botRoll = randint(1, 6)+randint(1, 6)
        if botRoll < 11:
            botRoll += choice([0, 1, 0])
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Villager Bot rolled: ``"+str(botRoll)+"``\nYou rolled: ``"+str(roll)+"``"))
        mult = 1+(randint(10, 30)/100)
        if inventories[str(ctx.message.author.id)] < 100:
            mult += 0.2
        rez = ceil(amount*mult)
        if rez-amount == 1:
            emerald = "emerald"
        else:
            emerald = "emeralds"
        if roll > botRoll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You won "+str(rez-amount)+" "+emerald+"! **|** Multiplier: "+str(int(mult*100))+"%"))
            inventories[str(ctx.message.author.id)] = inventories[str(ctx.message.author.id)]+(rez-amount)
        elif roll < botRoll:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="You lost! Villager Bot won "+str(amount)+" "+emerald+" from you."))
            inventories[str(ctx.message.author.id)] = inventories[str(ctx.message.author.id)]-amount
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="TIE! Maybe Villager Bot will just keep your emeralds anyway..."))
            
    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print("========== PERSON VOTED ON TOP.GG ==========")
        userID = data["user"]
        global inventories
        if str(userID) not in inventories:
            inventories[str(userID)] = 0
        inventories[str(userID)] = inventories[str(userID)] + 32
        user = self.bot.get_user(userID)
        await user.send(embed=discord.Embed(color=discord.Color.green(), description=choice(["You have been awarded 32 emeralds for voting for Villager Bot!",
                                                                                                  "You have recieved 32 emeralds for voting for Villager Bot!"])))
    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        print("========== DBL WEBHOOK TEST ==========")
        channel = self.bot.get_channel(643648150778675202)
        await channel.send(embed=discord.Embed(color=discord.Color.green(), description="DBL WEBHOOK TEST"))
        
def setup(bot):
    bot.add_cog(Currency(bot))
