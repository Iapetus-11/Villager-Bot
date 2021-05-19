from classyjson import ClassyDict
from discord.ext import commands
import aiofiles
import logging
import discord


def vb_intents() -> discord.Intents:
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


def setup_database(bot: commands.Bot, keys: ClassyDict) -> None:
    return asyncpg.create_pool(
        host=keys.database.host,  # where db is hosted
        database=keys.database.name,  # name of database
        user=keys.database.user,  # database username
        password=keys.database.passw,  # password which goes with user
        max_size=20,
        command_timeout=10,
    )


def load_text() -> ClassyDict:
    text = {}

    for filename in os.listdir("data/text"):
        with open(f"data/text/{filename}", "r", encoding="utf8") as f:
            text.update(json.load(f))

    return ClassyDict(text)


async def load_text_async() -> ClassyDict:
    text = {}

    for filename in os.listdir("data/text"):
        async with aiofiles.open(f"data/text/{filename}", "r", encoding="utf8") as f:
            text.update(json.loads(await f.read()))

    return ClassyDict(text)
