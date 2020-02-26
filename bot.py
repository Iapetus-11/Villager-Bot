from discord.ext import commands
import discord
import json
import psycopg2
import logging

logging.basicConfig(level=logging.WARNING)

bot = commands.AutoShardedBot(command_prefix="!!", help_command=None, case_insensitive=True)

cogs = ["data.global", "cogs.database.database", "cogs.owner.owner", "cogs.other.msgs", "cogs.other.errors", "cogs.other.events",
        "cogs.commands.fun", "cogs.commands.useful", "cogs.commands.mc", "cogs.commands.econ", "cogs.commands.admin"]

with open("data/keys.json", "r") as k: #load secret keys
    keys = json.load(k)
    
db = psycopg2.connect(host="localhost",database="villagerbot", user="pi", password=keys["postgres"])
cur = db.cursor()

async def banned(uid): #check if user is banned from bot
    cur.execute("SELECT id FROM bans WHERE bans.id='"+str(uid)+"'")
    entry = cur.fetchone()
    if entry == None:
        return False
    else:
        return True

@bot.check #global check (everything goes through this)
async def stay_safe(ctx):
    if not bot.is_ready():
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Hold on! Villager Bot is still starting up!"))
        return False
    if await banned(ctx.message.author.id):
        return False
    return ctx.message.author.id is not 639498607632056321 and not ctx.message.author.bot

#load cogs in cogs list
for cog in cogs:
    bot.load_extension(cog)

#actually start bot, it's a blocking call, nothing should go after this!
bot.run(keys["discord"], bot=True)
print("Bot has stopped!")