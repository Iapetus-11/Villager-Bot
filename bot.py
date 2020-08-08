import asyncio
import asyncpg
import discord
import json
import logging
from discord.ext import commands

global DEBUG
DEBUG = True

# set up basic logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)  # hide annoying asyncio warnings

with open("data/keys.json", "r") as k:  # load bot keys
    keys = json.load(k)

with open("data/config.json", "r") as c:  # load config
    config = json.load(c)


async def get_prefix(_bot, ctx):  # async function to fetch a prefix from the database
    if DEBUG:
        return "!!"

    if ctx.guild is None:
        return "!!"

    prefix = await _bot.db.fetchrow("SELECT prefix from server_configs WHERE gid = $1", ctx.guild.id)

    return "!!" if prefix is None else prefix[0]


bot = commands.AutoShardedBot(  # setup bot
    command_prefix=get_prefix,
    case_insensitive=True
)


async def send(self, location, message: str):
    try:
        await location.send(embed=discord.Embed(color=bot.cc, description=message))
        return True
    except discord.Forbidden:
        return False


bot.send = send.__get__(bot)  # bind send() to bot without subclassing bot


async def setup_database():  # init pool connection to database
    bot.db = await asyncpg.create_pool(
        host=config['database']['host'],
        database=config['database']['name'],
        user=config['database']['user'],
        password=keys['database'],
        command_timeout=5
    )

if not DEBUG:
    asyncio.get_event_loop().run_until_complete(setup_database())

bot.cc = discord.Color.green()  # embed color
bot.votes_topgg = 0
bot.votes_disbots = 0
bot.cmd_count = 0
bot.msg_count = 0
bot.start_time = None
bot.honey_buckets = None  # list of cooldowns for honey command (econ cog)

with json.load(open("data/data.json", "r", encoding='utf8')) as jj:  # load essential data from data.json
    bot.playing_list = jj['playing_list']  # list of games the bot can "play" in its status
    bot.cursed_images = jj['cursed_images']  # list of Minecraft cursed images
    bot.default_findables = jj['default_findables']  # items which can be found all the time
    bot.special_findables = jj['special_findables']  # items which can only be found via events
    bot.shop_items = jj['shop_items']  # items which are in the shop
    bot.emojis = jj['emojis']  # custom emojis which the bot uses
    bot.build_ideas = jj['build_ideas']  # list of build ideas for the !!buildidea command
    bot.emojified = jj['emojified']  # characters which can be emojified and their respective emojis
    bot.fun_langs = jj['fun_langs']  # fun languages for the text commands

# reverse enchant lang and make it its own lang (unenchantlang)
bot.fun_langs['unenchant'] = {}
for key in list(bot.fun_langs['enchant']):
    bot.fun_langs['unenchant'][bot.fun_langs['enchant'][key]] = key

bot.cog_list = [  # list of cogs which are to be loaded in the bot
    'cogs.cmds.mc',
    'cogs.cmds.mod'
]

for cog in bot.cog_list:  # load every cog in bot.cog_list
    bot.load_extension(cog)


async def is_bot_banned(uid):  # checks if a user has been botbanned
    return (await bot.db.fetchrow("SELECT bot_banned FROM users WHERE uid = $1", uid))[0]


@bot.check  # everythingggg goes through here
async def global_check(ctx):
    if not DEBUG:
        return bot.is_ready() and not await is_bot_banned(ctx.author.id)


bot.run(keys['discord'])  # run the bot, this is a blocking call
