from concurrent.futures import ThreadPoolExecutor
from discord.ext import commands
import classyjson as cj
import asyncio
import asyncpg
import discord
import logging
import random
import uvloop
import arrow

# send function/method for easy sending of embed messages with small amounts of text
async def send(_bot, location, message, respond=False, ping=False):
    embed = discord.Embed(color=_bot.d.cc, description=message)

    try:
        if respond and hasattr(location, "reply"):
            await location.reply(embed=embed, mention_author=ping)
        else:
            await location.send(embed=embed)

        return True
    except discord.Forbidden:
        return False


# get a lang for a given ctx object
async def get_lang(_bot, ctx):
    if ctx.guild is None:
        return _bot.langs.en

    lang = _bot.d.lang_cache.get(ctx.guild.id)

    if lang is None:
        lang = "en"

    return _bot.langs[lang]


# update the role of a member in the support server
async def update_support_member_role(_bot, member):
    support_guild = _bot.get_guild(_bot.d.support_server_id)
    role_map_values = list(_bot.d.role_mappings.values())
    db = _bot.get_cog("Database")
    roles = []

    for role in member.roles:
        if role.id not in role_map_values and role.id != _bot.d.support_server_id:
            roles.append(role)

    pickaxe_role = _bot.d.role_mappings.get(await db.fetch_pickaxe(member.id))
    if pickaxe_role is not None:
        roles.append(support_guild.get_role(pickaxe_role))

    if await db.fetch_item(member.id, "Bane Of Pillagers Amulet") is not None:
        roles.append(support_guild.get_role(_bot.d.role_mappings.get("BOP")))

    if roles != member.roles:
        try:
            await member.edit(roles=roles)
        except Exception:
            pass


async def send_tip(_bot, ctx):
    await asyncio.sleep(1)
    await ctx.send(f"{random.choice(ctx.l.misc.tip_intros)} {random.choice(ctx.l.misc.tips)}")


def update_fishing_prices(_bot):
    for fish in _bot.d.fishing.fish.values():
        fish.current = random.choice(fish.value)


if __name__ == "__main__":
    # use uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # set up basic logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # hide annoying asyncio info
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)  # hide annoying gateway info
    logger = logging.getLogger("main")

    logger.info("loading private keys...")
    with open("data/keys.json", "r") as k:  # load bot keys
        keys = cj.load(k)

    async def get_prefix(_bot, ctx):  # async function to fetch a prefix from the database
        if ctx.guild is None:
            return _bot.d.default_prefix

        prefix = _bot.d.prefix_cache.get(ctx.guild.id)

        return _bot.d.default_prefix if prefix is None else prefix

    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    intents.bans = True
    intents.emojis = False
    intents.integrations = False
    intents.webhooks = False
    intents.invites = False
    intents.voice_states = False
    intents.presences = True
    intents.messages = True
    # intents.guild_messages = True
    # intents.dm_messages = True
    intents.reactions = True
    # intents.guild_reactions = True
    # intents.dm_reactions = True
    intents.typing = False
    # intents.guild_typing = False
    # intents.dm_typing = False

    bot = commands.AutoShardedBot(  # setup bot
        command_prefix=get_prefix,
        case_insensitive=True,
        intents=intents,
        help_command=None,
    )

    bot.logger = logger

    bot.send = send.__get__(bot)
    bot.get_lang = get_lang.__get__(bot)
    bot.update_support_member_role = update_support_member_role.__get__(bot)
    bot.update_fishing_prices = update_fishing_prices.__get__(bot)

    async def setup_database():  # init pool connection to database
        logger.info("setting up connection to database and db pool...")
        bot.db = await asyncpg.create_pool(
            host=keys.database.host,  # where db is hosted
            database=keys.database.name,  # name of database
            user=keys.database.user,  # database username
            password=keys.database.passw,  # password which goes with user
            max_size=20,
            command_timeout=10,
        )

    asyncio.get_event_loop().run_until_complete(setup_database())

    logger.info("loading villager bot text from data/text.json...")
    with open("data/text.json", "r", encoding="utf8") as l:
        bot.langs = cj.load(l)  # turns it into dot accessible dicts for ez access ~~nice dict bro~~

    logger.info("loading villager bot constant data from data/data.json...")
    with open("data/data.json", "r", encoding="utf8") as d:
        bot.d = cj.load(d)  # cj automatically turns json into sets of nested classes and attributes for easy access

    bot.d.cc = discord.Color.green()  # embed color

    bot.k = keys
    bot.k.fernet = bot.k.fernet.encode("utf-8")

    bot.d.votes_topgg = 0
    bot.d.cmd_count = 0
    bot.d.msg_count = 0
    bot.d.start_time = arrow.utcnow()

    bot.d.miners = {}  # {user_id: commands}
    bot.d.honey_buckets = None  # list of cooldowns for honey command (econ cog)
    bot.d.mining.pickaxes = list(bot.d.mining.yields_pickaxes)[::-1]  # get list of pickaxe types from best to worst
    bot.d.pillagers = {}  # {user_id: pillages}
    bot.d.pillages = {}  # {user_id: times_pillaged}
    bot.d.chuggers = {}  # {user_id: [potion, potion]}
    bot.d.cmd_lb = {}  # {user_id: command_count}

    bot.d.pause_econ = {}  # {uid: starttime}
    bot.d.spawn_queue = {}  # {ctx: starttime}

    bot.d.rcon_cache = {}  # {uid: rcon_client}

    bot.d.disabled_cmds = {}  # {gid: [disabled cmds]}

    bot.d.ban_cache = []  # [uid, uid,..]
    bot.d.prefix_cache = {}  # {gid: 'prefix'}
    bot.d.lang_cache = {}  # {gid: 'lang'}

    bot.d.additional_mcservers = []
    bot.d.mcserver_list = []

    bot.d.fun_langs.unenchant = {v: k for k, v in bot.d.fun_langs.enchant.items()}  # reverse dict to create unenchantment lang

    bot.owner_locked = False

    bot.cog_list = [  # list of cogs which are to be loaded in the bot
        "cogs.core.database",
        "cogs.core.events",
        "cogs.cmds.useful",
        "cogs.cmds.owner",
        "cogs.cmds.mc",
        "cogs.cmds.mod",
        "cogs.cmds.fun",
        "cogs.cmds.econ",
        "cogs.cmds.config",
        "cogs.other.mobs",
        "cogs.other.status",
        "cogs.other.statcord",
        "cogs.other.webhooks",
    ]

    for cog in bot.cog_list:  # load every cog in bot.cog_list
        logger.info(f"loading extension: {cog}")
        bot.load_extension(cog)

    @bot.check  # everythingggg goes through here
    async def global_check(ctx):
        ctx.l = await bot.get_lang(ctx)

        # if bot is locked down to only accept commands from owner
        if bot.owner_locked and ctx.author.id != 536986067140608041:
            ctx.custom_err = "ignore"
        elif ctx.author.id in bot.d.ban_cache:  # if command author is bot banned
            ctx.custom_err = "bot_banned"
        elif not bot.is_ready():  # if bot hasn't completely started up yet
            ctx.custom_err = "not_ready"
        elif ctx.guild is not None and ctx.command.name in bot.d.disabled_cmds.get(ctx.guild.id, []):  # if command is disabled
            ctx.custom_err = "disabled"

        if hasattr(ctx, "custom_err"):
            return False

        # update the leaderboard + session command count
        try:
            bot.d.cmd_lb[ctx.author.id] += 1
        except KeyError:
            bot.d.cmd_lb[ctx.author.id] = 1

        bot.d.cmd_count += 1

        if ctx.command.cog and ctx.command.cog.__cog_name__ == "Econ":  # make sure it's an econ command
            if bot.d.pause_econ.get(ctx.author.id) is not None:
                ctx.custom_err = "econ_paused"
                return False

            if random.randint(1, 40) == 1:  # spawn mob
                if ctx.command._buckets._cooldown is not None and ctx.command._buckets._cooldown.per >= 2:
                    bot.d.spawn_queue[ctx] = arrow.utcnow()

        if random.randint(1, bot.d.tip_chance) == 1:
            bot.loop.create_task(send_tip(ctx))

        return True

    with ThreadPoolExecutor() as bot.tpool:
        bot.run(keys.discord)  # run the bot, this is a blocking call
