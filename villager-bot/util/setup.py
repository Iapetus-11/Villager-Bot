from classyjson import ClassyDict
import asyncpg
import logging
import discord
import random
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


def setup_karen_logging():
    logger = logging.getLogger("KAREN")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[Karen] %(levelname)s: %(message)s"))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


async def setup_database_pool(secrets: ClassyDict, max_size: int):
    return await asyncpg.create_pool(
        host=secrets.database.host,  # where db is hosted
        database=secrets.database.name,  # name of database
        user=secrets.database.user,  # database username
        password=secrets.database.auth,  # password which goes with user
        max_size=max_size,
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
        data = ClassyDict(orjson.loads(f.read()))

    mod_data(data)
    return data


def update_fishing_prices(d: ClassyDict):
    for fish in d.fishing.fish.values():
        fish.current = random.randint(*fish.value)


def mod_data(d: ClassyDict) -> None:
    # make discord.py color class from value in data.json
    d.cc = getattr(discord.Color, d.embed_color)()

    # update fishing data, generate fishing weights
    update_fishing_prices(d)
    fishes = d.fishing.fish_ids = list(d.fishing.fish.keys())
    d.fishing.fish_weights = [(len(fishes) - fish_data.rarity) ** d.fishing.exponent for fish_data in d.fishing.fish.values()]

    # get list of pickaxe types from best to worst
    d.mining.pickaxes = list(d.mining.yields_pickaxes)[::-1]

    # reverse dict to create unenchantment lang
    d.fun_langs.unenchant = {v: k for k, v in d.fun_langs.enchant.items()}
