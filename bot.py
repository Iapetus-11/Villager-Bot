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
    gid = ctx.guild.id
    prefix = await bot.db.fetchrow(f"SELECT prefix FROM prefixes WHERE prefixes.gid='{gid}'")
    if prefix is None:
        async with bot.db.acquire() as con:
            await con.execute(f"INSERT INTO prefixes VALUES ('{gid}', '!!')")
        return "!!"
    # return commands.when_mentioned_or(prefix[0])(bot, ctx)
    return prefix[0]


bot = commands.AutoShardedBot(command_prefix=get_prefix, help_command=None, case_insensitive=True, max_messages=9999)

async def setup_db():
    bot.db = await asyncpg.create_pool(host="localhost", database="villagerbot", user="pi", password=keys["postgres"], command_timeout=5)

asyncio.get_event_loop().run_until_complete(setup_db())

# data.global needs to be loaded FIRST, then database and owner as they are dependant upon GLOBAL
bot.cog_list = ["data.global",
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
    entry = await bot.db.fetchrow(f"SELECT id FROM bans WHERE bans.id='{str(uid)}'")
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
