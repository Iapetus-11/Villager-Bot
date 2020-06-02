import json
import asyncpg
import asyncio
import logging
import discord
from discord.ext import commands
from random import randint, choice


logging.basicConfig(level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

tips = ["Did you know you can get emeralds from voting for us on [top.gg](https://top.gg/bot/639498607632056321)?",
        "If you ever need more help, don't forget to check out the [support server](https://discord.gg/39DwwUV)!",
        "Have any suggestions? Use the suggestion channel in our [support server](https://discord.gg/39DwwUV)!",
        "In need of **emeralds**? Check out the #paid-stuff channel on the [support server](https://discord.gg/39DwwUV)!"]

with open("data/keys.json", "r") as k:  # Loads secret keys
    keys = json.load(k)


# Fetch prefix from db, also, self(in this context) is bot
async def get_prefix(bot, ctx):
    if ctx.guild is None:
        return "!!"
    prefix = await bot.db.fetchrow("SELECT prefix FROM prefixes WHERE prefixes.gid=$1", ctx.guild.id)
    if prefix is None:
        async with bot.db.acquire() as con:
            await con.execute("INSERT INTO prefixes VALUES ($1, $2)", ctx.guild.id, "!!")
        return "!!"
    return prefix[0]


bot = commands.AutoShardedBot(shard_count=8, command_prefix=get_prefix, help_command=None, case_insensitive=True, max_messages=512)


async def setup_db():
    bot.db = await asyncpg.create_pool(host="localhost", database="villagerbot", user="pi", password=keys["postgres"],
                                       command_timeout=5)


asyncio.get_event_loop().run_until_complete(setup_db())

# data.global needs to be loaded FIRST, then database and owner as they and most other things are dependant upon global.py and database.py
bot.cog_list = ["cogs.other.global",
                "cogs.database.database",
                "cogs.owner.owner",
                "cogs.other.errors",
                "cogs.other.msgs",
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

    _global = bot.get_cog("Global")
    _global.cmd_count += 1
    _global.cmd_vect[0] += 1

    if ctx.author.id in list(_global.command_leaderboard):
        _global.command_leaderboard[ctx.author.id] += 1
    else:
        _global.command_leaderboard[ctx.author.id] = 1

    del _global

    if not bot.is_ready():
        await ctx.send(
            embed=discord.Embed(color=discord.Color.green(), description="Hold on! Villager Bot is still starting up!"))
        return False

    done_event = False
    if floor(randint(0, 75)*(ctx.guild.member_count/2)) == 2: # Excuse me sir, this is a wendys
        return # Just for now
        done_event = True
        self.bot.get_cog("MobSpawning").do_event.append(ctx)

    if randint(0, 150) == 25 and not done_event:
        if str(ctx.command) not in ["eval", "awaiteval", "help", "ping", "uptime", "stats", "vote", "invite", "purge"]:
            if ctx.guild is None or await bot.get_cog("Database").get_do_tips(ctx.guild.id):
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"**{choice(['Handy Dandy Tip:', 'Cool Tip:', 'Pro Tip:'])}** {choice(tips)}"))

    del done_event

    return not ctx.message.author.bot and not await banned(ctx.message.author.id)


# Actually start bot, it's a blocking call, nothing should go after this!
bot.run(keys["discord"], bot=True)
