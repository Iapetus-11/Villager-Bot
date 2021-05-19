from classyjson import ClassyDict
from discord.ext import commands
import aiofiles
import asyncpg
import logging
import discord
import os


def villager_bot_intents() -> discord.Intents:
    return discord.Intents(
        guilds=True,
        members=True,
        bans=True,
        emojis=False,
        integrations=False,
        webhooks=False,
        invites=False,
        voice_states=False,
        presences=True,
        messages=True,
        reactions=True,
        typing=False,
    )


def setup_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")
    # logging.getLogger("asyncio").setLevel(logging.WARNING)  # hide annoying asyncio info
    # logging.getLogger("discord.gateway").setLevel(logging.WARNING)  # hide annoying gateway info
    return logging.getLogger("main")


def setup_database(secrets: ClassyDict) -> None:
    return asyncpg.create_pool(
        host=secrets.database.host,  # where db is hosted
        database=secrets.database.name,  # name of database
        user=secrets.database.user,  # database username
        password=secrets.database.passw,  # password which goes with user
        max_size=10,
        command_timeout=10,
    )
