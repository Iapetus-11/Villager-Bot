from discord.ext import commands
import discord
import json
import psycopg2
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

with open("data/keys.json", "r") as k:  # Loads secret keys
    keys = json.load(k)

db = psycopg2.connect(host="localhost", database="villagerbot", user="pi", password=keys["postgres"])
cur = db.cursor()


# Fetch prefix from db
def getPrefix(self, message):
    if message.guild is None:
        return "!!"
    gid = message.guild.id
    cur.execute("SELECT prefix FROM prefixes WHERE prefixes.gid='"+str(gid)+"'")
    prefix = cur.fetchone()
    if prefix is None:
        cur.execute("INSERT INTO prefixes VALUES ('"+str(gid)+"', '!!')")
        db.commit()
        return "!!"
    return prefix[0]


bot = commands.AutoShardedBot(shard_count=2, command_prefix=getPrefix, help_command=None, case_insensitive=True, max_messages=9999)

# data.global needs to be loaded FIRST, then database and owner as they are dependant upon GLOBAL
cogs = ["data.global",
        "cogs.database.database",
        "cogs.owner.owner",
        "cogs.other.msgs",
        "cogs.other.errors",
        "cogs.other.events",
        "cogs.other.loops",
        "cogs.commands.fun",
        "cogs.commands.useful",
        "cogs.commands.mc",
        "cogs.commands.econ",
        "cogs.commands.admin",
        "cogs.commands.settings"]

# Load cogs in cogs list
for cog in cogs:
    bot.load_extension(cog)


async def banned(uid):  # Check if user is banned from bot
    cur.execute(f"SELECT id FROM bans WHERE bans.id='{str(uid)}'")
    entry = cur.fetchone()
    if entry is None:
        return False
    else:
        return True


@bot.check  # Global check (everything goes through this)
async def stay_safe(ctx):
    if not bot.is_ready():
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description="Hold on! Villager Bot is still starting up!"))
        return False
    bot.get_cog("Global").cmd_count += 1
    bot.get_cog("Global").cmd_vect += 1
    if await banned(ctx.message.author.id):
        return False
    return not ctx.message.author.bot


# Actually start bot, it's a blocking call, nothing should go after this!
bot.run(keys["discord"], bot=True)
print("Bot has stopped!")
