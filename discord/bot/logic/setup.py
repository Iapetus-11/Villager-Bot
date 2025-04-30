import json
import logging
import os
import random
import subprocess
from typing import Collection

import colorlog
import discord

from bot.models.data import Data
from bot.models.logging_config import LoggingConfig
from bot.models.secrets import Secrets
from bot.models.translation import Translation
from bot.utils.code import format_exception


def load_data() -> Data:
    with open("../common/data.json", "r") as f:
        return Data.model_validate_json(f.read())


def load_translations(disabled_translations: Collection[str]) -> dict[str, Translation]:
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
    with open("secrets.json", "r") as f:
        return Secrets.model_validate_json(f.read())


def update_fishing_prices(data: Data):
    for fish in data.fishing.fish.values():
        fish.current = random.randint(*fish.value)


def get_cluster_id() -> int:
    if os.environ.get("WITHIN_DOCKER", "").lower() not in ["1", "true"]:
        return 0

    result = subprocess.run(["./docker-replica-id.sh"], stdin=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception("Non-zero return code from docker-replica-id.sh")

    return int(result.stdout.strip(b" \n")) - 1


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


def setup_logging(name: str, config: LoggingConfig) -> logging.Logger:
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
    handler.setLevel(config.level)

    logger = logging.getLogger(name)
    logger.setLevel(config.level)

    for item in logging.root.manager.loggerDict.values():
        if isinstance(item, logging.Logger):
            item.addHandler(handler)

    for name, override in config.overrides.items():
        logging.getLogger(name).setLevel(override.level)

    return logger
