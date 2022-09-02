import json
import os
import random

import discord

from common.models.data import Data

from bot.models.secrets import Secrets
from bot.models.translation import Translation
from common.utils.code import format_exception


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


def load_translations() -> dict[str, Translation]:
    translations = dict[str, Translation]()

    for filename in os.listdir("bot/data/text"):
        lang_name = filename.split(".")[0]

        try:
            with open(f"bot/data/text/{filename}", "r", encoding="utf8") as f:
                data = json.load(f)

            translations[lang_name] = Translation(**data[lang_name])
        except Exception as e:
            print(f"An error occurred while loading the {lang_name} translation: {format_exception(e)}")

    if "en" not in translations:
        raise Exception("Default translation unable to be loaded.")

    return translations


def load_secrets() -> Secrets:
    return Secrets.parse_file("bot/secrets.json")


def update_fishing_prices(data: Data):
    for fish in data.fishing.fish.values():
        fish.current = random.randint(*fish.value)
