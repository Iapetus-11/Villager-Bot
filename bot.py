from discord.ext import commands
import discord
import json
import asyncpg
import asyncio
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

with open("data/keys.json", "r") as k:  # Loads secret keys
    keys = json.load(k)

# Fetch prefix from db, also, self(in this context) is bot
async def get_prefix(bot, ctx):
    if ctx.guild is None:
        return "!!"
    prefix = await bot.db.fetchrow("SELECT prefix FROM prefixes WHERE prefixes.gid=$1", ctx.guild.id)
    if prefix is None:
        async with bot.db.acquire() as con:
            await con.execute("INSERT INTO prefixes VALUES ($1, $2)", gid, "!!")
        return "!!"
    return prefix[0]


bot = commands.AutoShardedBot(command_prefix=get_prefix, help_command=None, case_insensitive=True, max_messages=9999)

async def setup_db():
    bot.db = await asyncpg.create_pool(host="localhost", database="villagerbot", user="pi", password=keys["postgres"], command_timeout=5)

asyncio.get_event_loop().run_until_complete(setup_db())

# data.global needs to be loaded FIRST, then database and owner as they and most other things are dependant upon global.py and database.py
bot.cog_list = ["cogs.other.global",
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
for cog in bot.cog_list:
    bot.load_extension(cog)


async def banned(uid):  # Check if user is banned from bot
    entry = await bot.db.fetchrow("SELECT id FROM bans WHERE bans.id=$1", uid)
    if entry is None:
        return False
    return True


@bot.check  # Global check (everything goes through this)
async def stay_safe(ctx):
    await bot.get_cog("Database").increment_vault_max(ctx.author.id)
    bot.get_cog("Global").cmd_count += 1
    bot.get_cog("Global").cmd_vect += 1
    if not bot.is_ready():
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description="Hold on! Villager Bot is still starting up!"))
        return False
    if await banned(ctx.message.author.id):
        return False
    return not ctx.message.author.bot


# Actually start bot, it's a blocking call, nothing should go after this!
bot.run(keys["discord"], bot=True)
