import asyncio
import asyncpg
import discord
import json
import logging
from discord.ext import commands
import classyjson

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
    return '/'

    if DEBUG:
        return '/'

    if ctx.guild is None:
        return '/'

    prefix = await _bot.db.fetchrow("SELECT prefix from server_configs WHERE gid = $1", ctx.guild.id)

    return '/' if prefix is None else prefix[0]


bot = commands.AutoShardedBot(  # setup bot
    command_prefix=get_prefix,
    case_insensitive=True
)


async def send(self, location, message: str):  # send function/method for easy sending of embed messages with small amounts of text
    try:
        await location.send(embed=discord.Embed(color=bot.d.cc, description=message))
        return True
    except discord.Forbidden:
        return False


bot.send = send.__get__(bot)  # bind send() to bot without subclassing bot


async def setup_database():  # init pool connection to database
    bot.db = await asyncpg.create_pool(
        host=config['database']['host'],  # where db is hosted
        database=config['database']['name'],  # name of database
        user=config['database']['user'],  # database username
        password=keys['database'],  # password which goes with user
        command_timeout=5
    )

asyncio.get_event_loop().run_until_complete(setup_database())

with open('data/data.json', 'r', encoding='utf8') as d:
    bot.d = classyjson.load(d)  # classyjson automatically turns json into sets of nested classes and attributes for easy access

bot.d.cc = discord.Color.green()  # embed color

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

bot.d.splash_logo = 'http://172.10.17.177/images/villagerbotsplash1.png'
bot.d.support = 'https://discord.gg/39DwwUV'
bot.d.invite = 'https://discord.com/oauth2/authorize?client_id=639498607632056321&permissions=8&scope=bot'

bot.d.fun_langs.unenchant = {}
for key in list(bot.d.fun_langs.enchant):  # reverse the enchant lang to get the unenchant lang
    bot.d.fun_langs.unenchant[bot.d.fun_langs.enchant[key]] = key

bot.cog_list = [  # list of cogs which are to be loaded in the bot
    'cogs.core.database',
    'cogs.core.events',
    'cogs.cmds.useful',
    'cogs.cmds.mc',
    'cogs.cmds.mod',
    'cogs.cmds.fun',
    'cogs.cmds.econ'
]

for cog in bot.cog_list:  # load every cog in bot.cog_list
    bot.load_extension(cog)


async def is_bot_banned(uid):  # checks if a user has been botbanned
    user = await bot.db.fetchrow('SELECT bot_banned FROM users WHERE uid = $1', uid)
    if user is not None:
        return user['bot_banned']
    else:
        return False


@bot.check  # everythingggg goes through here
async def global_check(ctx):
    if DEBUG:
        if ctx.channel.id in (643648150778675202, 750788275383435395,):
            return True
        return False

    return bot.is_ready() and not await is_bot_banned(ctx.author.id)


bot.run(keys['discord'])  # run the bot, this is a blocking call
