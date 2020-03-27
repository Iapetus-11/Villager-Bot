from discord.ext import commands
import discord
import json
import asyncpg
import logging

logging.basicConfig(level=logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

# Fetch prefix from db
def getPrefix(self, message):
    if message.guild is None:
        return "!!"
    gid = message.guild.id
    prefix = await self.bot.db.fetchrow(f"SELECT prefix FROM prefixes WHERE prefixes.gid='{gid}'")
    if prefix is None:
        await self.bot.db.execute(f"INSERT INTO prefixes VALUES ('{gid}', '!!')")
        await self.bot.db.commit()
        return "!!"
    return prefix[0]

with open("data/keys.json", "r") as k:  # Loads secret keys
    keys = json.load(k)

bot = commands.AutoShardedBot(command_prefix=getPrefix, help_command=None, case_insensitive=True, max_messages=9999)

async def setup_db():
    bot.db = await asyncpg.connect(host="localhost", database="villagerbot", user="pi", password=keys["postgres"])

asyncio.get_event_loop().run_until_complete(setup_db())

bot.cogs = ["data.global",
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

for cog in bot.cogs:
    bot.load_extension(cog)

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
print("Bot has stopped somehow...")
