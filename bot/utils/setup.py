import json
import logging
import os
import random

import discord

from common.models.data import Data

from bot.models.secrets import Secrets
from bot.models.translation import Translation


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
        message_content=True,
    )


def setup_logging(cluster_id: int) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format=f"[{cluster_id}] %(levelname)s: %(message)s")

    logging.getLogger("asyncio").setLevel(logging.WARNING)  # hide annoying asyncio info
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)  # hide annoying gateway info

    return logging.getLogger("bot")


def load_translations() -> dict[str, Translation]:
    translations = dict[str, Translation]()

    for filename in os.listdir("bot/data/text"):
        lang_name = filename.split(".")[0]

        with open(f"bot/data/text/{filename}", "r", encoding="utf8") as f:
            data = json.load(f)

        translations[lang_name] = Translation(**data[lang_name])

    return translations


def load_secrets() -> Secrets:
    return Secrets.parse_file("bot/secrets.json")


def update_fishing_prices(data: Data):
    for fish in data.fishing.fish.values():
        fish.currrent = random.randint(*fish.value)
