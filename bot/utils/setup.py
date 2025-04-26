import json
import os
import random

import discord

from bot.models.data import Data
from bot.utils.code import format_exception

from bot.models.secrets import Secrets
from bot.models.translation import Translation


import logging

import colorlog

from bot.models.logging_config import LoggingConfig


def villager_bot_intents() -> discord.Intents:
    return discord.Intents(
        guilds=True,
        members=True,
        moderation=False,
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


def load_data() -> Data:
    return Data.parse_file("common/data/data.json")


def setup_logging(name: str, config: LoggingConfig) -> logging.Logger:
    level = logging.getLevelName(config.level)

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%m-%d-%y %H:%M:%S",
            log_colors={
                "DEBUG": "white",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
            reset=False,
        ),
    )
    handler.setLevel(level)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    for item in logging.root.manager.loggerDict.values():
        if isinstance(item, logging.Logger):
            item.addHandler(handler)

    for name, override in config.overrides.items():
        logging.getLogger(name).setLevel(logging.getLevelName(override.level))

    return logger


def load_translations(disabled_translations: list[str]) -> dict[str, Translation]:
    translations = dict[str, Translation]()

    for filename in os.listdir("bot/data/text"):
        lang_name = filename.split(".")[0]

        if lang_name in disabled_translations:
            continue

        try:
            with open(f"bot/data/text/{filename}", "r", encoding="utf8") as f:
                data = json.load(f)

            translations[lang_name] = Translation(**data[lang_name])
        except Exception as e:
            print(  # noqa: T201
                f"An error occurred while loading the {lang_name} translation: {format_exception(e)}",
            )

    if "en" not in translations:
        raise Exception("Default translation unable to be loaded.")

    return translations


def load_secrets() -> Secrets:
    return Secrets.parse_file("bot/secrets.json")


def update_fishing_prices(data: Data):
    for fish in data.fishing.fish.values():
        fish.current = random.randint(*fish.value)
