import logging

import colorlog

from common.models.data import Data
from common.models.logging_config import LoggingConfig


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

    for _, item in logging.root.manager.loggerDict.items():
        if isinstance(item, logging.Logger):
            item.addHandler(handler)

    for name, override in config.overrides.items():
        logging.getLogger(name).setLevel(logging.getLevelName(override.level))

    return logger
