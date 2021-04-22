from discord.ext import commands
import discord
import logging
import asyncpg

from util.cj import ClassyDict


def villager_bot_intents() -> discord.Intents:
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

    return intents


def setup_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # hide annoying asyncio info
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)  # hide annoying gateway info
    return logging.getLogger("main")


async def setup_database(bot: commands.AutoShardedBot, keys: ClassyDict) -> None:  # init pool connection to database
    bot.db = await asyncpg.create_pool(
        host=keys.database.host,  # where db is hosted
        database=keys.database.name,  # name of database
        user=keys.database.user,  # database username
        password=keys.database.passw,  # password which goes with user
        max_size=20,
        command_timeout=10,
    )
