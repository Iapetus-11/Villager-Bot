from classyjson import ClassyDict
from discord.ext import commands
import aiofiles
import asyncpg
import logging
import discord
import orjson
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


def setup_logging(shard_ids: list) -> logging.Logger:
    shard_range_str = str(shard_ids[0]).rjust(2, "0") + "-" + str(shard_ids[-1]).rjust(2, "0")
    logging.basicConfig(level=logging.INFO, format=f"[{shard_range_str}] %(levelname)s: %(message)s")
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # hide annoying asyncio info
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)  # hide annoying gateway info
    return logging.getLogger("main")


async def setup_database(secrets: ClassyDict):
    return await asyncpg.create_pool(
        host=secrets.database.host,  # where db is hosted
        database=secrets.database.name,  # name of database
        user=secrets.database.user,  # database username
        password=secrets.database.auth,  # password which goes with user
        max_size=3,
        min_size=3,
        command_timeout=10,
    )


def load_text() -> ClassyDict:
    text = {}

    for filename in os.listdir("data/text"):
        with open(f"data/text/{filename}", "r", encoding="utf8") as f:
            text.update(orjson.loads(f.read()))

    return ClassyDict(text)


def load_secrets() -> ClassyDict:
    with open("../secrets.json", "r", encoding="utf8") as f:
        return ClassyDict(orjson.loads(f.read()))


def load_data() -> ClassyDict:
    with open("data/data.json", "r", encoding="utf8") as f:
        return ClassyDict(orjson.loads(f.read()))
