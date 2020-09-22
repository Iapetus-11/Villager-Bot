from discord.ext import commands
import classyjson as cj
import asyncio
import asyncpg
import discord
import logging


# set up basic logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)  # hide annoying asyncio warnings

with open("data/keys.json", "r") as k:  # load bot keys
    keys = cj.load(k)

with open("data/config.json", "r") as c:  # load config
    config = cj.load(c)

async def get_prefix(_bot, ctx):  # async function to fetch a prefix from the database
    if ctx.guild is None:
        return _bot.d.default_prefix

    prefix = _bot.d.prefix_cache.get(ctx.guild.id)

    return _bot.d.default_prefix if prefix is None else prefix[0]


bot = commands.AutoShardedBot(  # setup bot
    command_prefix=get_prefix,
    case_insensitive=True,
    #help_command=None
)

async def send(_bot, location, message: str):  # send function/method for easy sending of embed messages with small amounts of text
    try:
        await location.send(embed=discord.Embed(color=_bot.d.cc, description=message))
        return True
    except discord.Forbidden:
        return False


async def get_lang(_bot, ctx):
    if ctx.guild is None:
        return _bot.langs.en_us

    lang = _bot.d.lang_cache.get(ctx.guild.id)

    if lang is None:
        lang = 'en_us'

    return _bot.langs[lang]


bot.send = send.__get__(bot)  # bind send() to bot without subclassing bot
bot.get_lang = get_lang.__get__(bot)

async def setup_database():  # init pool connection to database
    bot.db = await asyncpg.create_pool(
        host=config['database']['host'],  # where db is hosted
        database=config['database']['name'],  # name of database
        user=config['database']['user'],  # database username
        password=keys['database'],  # password which goes with user
        command_timeout=5
    )

asyncio.get_event_loop().run_until_complete(setup_database())

with open('data/text.json', 'r', encoding='utf8') as l:
    bot.langs = cj.load(l)  # turns it into dot accessible dicts for ez access ~~nice dict bro~~

with open('data/data.json', 'r', encoding='utf8') as d:
    bot.d = cj.load(d)  # cj automatically turns json into sets of nested classes and attributes for easy access

bot.d.cc = discord.Color.green()  # embed color
bot.d.k = keys.ap

bot.d.votes_topgg = 0
bot.d.votes_disbots = 0
bot.d.cmd_count = 0
bot.d.msg_count = 0
bot.d.start_time = None

bot.d.miners = {}  # {user_id: commands}
bot.d.honey_buckets = None  # list of cooldowns for honey command (econ cog)
bot.d.mining.pickaxes = list(reversed(list(bot.d.mining.yields_pickaxes)))  # get list of pickaxe types from best to worst
bot.d.findables = bot.d.special_findables + bot.d.default_findables
bot.d.pillagers = {}  # {user_id: daily_pillages}
bot.d.chuggers = {}  # {user_id: [potion, potion]}

bot.d.ban_cache = []  # [uid, uid,..]
bot.d.prefix_cache = {}  # {gid: 'prefix'}
bot.d.lang_cache = {}  # {gid: 'lang'}

bot.d.fun_langs.unenchant = {}
for key in list(bot.d.fun_langs.enchant):  # reverse the enchant lang to get the unenchant lang
    bot.d.fun_langs.unenchant[bot.d.fun_langs.enchant[key]] = key

bot.cog_list = [  # list of cogs which are to be loaded in the bot
    'cogs.core.database',
    'cogs.core.events',
    #'cogs.cmds.useful',
    'cogs.cmds.owner',
    'cogs.cmds.mc',
    'cogs.cmds.mod',
    'cogs.cmds.fun',
    'cogs.cmds.econ'
]

for cog in bot.cog_list:  # load every cog in bot.cog_list
    bot.load_extension(cog)

@bot.check  # everythingggg goes through here
async def global_check(ctx):
    if bot.is_ready() and ctx.author.id not in bot.d.ban_cache:
        ctx.l = await bot.get_lang(ctx)
        return True

    return False


bot.run(keys['discord'])  # run the bot, this is a blocking call
