import asyncio
import asyncpg
import discord
import json
import logging
from discord.ext import commands

global DEBUG
DEBUG = True  # disables db stuff and some other stuff

# set up basic logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)  # hide annoying asyncio warnings

with open("data/keys.json", "r") as k:  # load bot keys
    keys = json.load(k)

with open("data/config.json", "r") as c:  # load config
    config = json.load(c)


async def get_prefix(_bot, ctx):  # async function to fetch a prefix from the database
    if DEBUG:
        return ","

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
        host=config['database']['host'],  # where db is hosted
        database=config['database']['name'],  # name of database
        user=config['database']['user'],  # database username
        password=keys['database'],  # password which goes with user
        command_timeout=5
    )

if not DEBUG:
    asyncio.get_event_loop().run_until_complete(setup_database())

class Data:
    def __init__(self):
        self.cc = discord.Color.green()  # embed color

        self.votes_topgg = 0
        self.votes_disbots = 0
        self.cmd_count = 0
        self.msg_count = 0
        self.start_time = None

        self.honey_buckets = None  # list of cooldowns for honey command (econ cog)

        self.splash_logo = 'http://172.10.17.177/images/villagerbotsplash1.png'

        with open("data/data.json", "r", encoding='utf8') as d:  # load essential data from data.json
            jj = json.load(d)
            self.jj = jj

        self.custom_emojis = jj['emojis']  # custom emojis which the bot uses

        class Emojis:
            def __init__(_self):
                _self.online = self.custom_emojis['online']
                _self.offline = self.custom_emojis['offline']

                _self.emerald = self.custom_emojis['emerald']
                _self.emerald_block = self.custom_emojis['emerald_block']
                _self.netherite = self.custom_emojis['netherite']

        self.emojis = Emojis()

        self.default_findables = jj['default_findables']  # items which can be found all the time
        self.special_findables = jj['special_findables']  # items which can only be found via events
        self.shop_items = jj['shop_items']  # items which are in the shop

        self.playing_list = jj['playing_list']  # list of games the bot can "play" in its status
        self.cursed_images = jj['cursed_images']  # list of Minecraft cursed images
        self.build_ideas = jj['build_ideas']  # list of build ideas for the !!buildidea command
        self.emojified = jj['emojified']  # characters which can be emojified and their respective emojis
        self.fun_langs = jj['fun_langs']  # fun languages for the text commands

        self.gamble_sayings = jj['gamble']  # stuff for gamble command
        self.begging_sayings = jj['begging']  # text responses for begging command

        # reverse enchant lang and make it its own lang (unenchantlang)
        self.fun_langs['unenchant'] = {}
        for key in list(self.fun_langs['enchant']):
            self.fun_langs['unenchant'][self.fun_langs['enchant'][key]] = key

bot.d = Data()

bot.cog_list = [  # list of cogs which are to be loaded in the bot
    'cogs.core.events',
    'cogs.cmds.mc',
    'cogs.cmds.mod',
    'cogs.cmds.fun',
    'cogs.cmds.econ'
]

for cog in bot.cog_list:  # load every cog in bot.cog_list
    bot.load_extension(cog)


async def is_bot_banned(uid):  # checks if a user has been botbanned
    return (await bot.db.fetchrow("SELECT bot_banned FROM users WHERE uid = $1", uid))[0]


@bot.check  # everythingggg goes through here
async def global_check(ctx):
    if DEBUG:
        return True

    return bot.is_ready() and not await is_bot_banned(ctx.author.id)


bot.run(keys['discord'])  # run the bot, this is a blocking call
