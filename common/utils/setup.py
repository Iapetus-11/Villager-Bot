import logging

import colorlog

from common.models.data import Data


def load_data() -> Data:
    return Data.parse_file("common/data/data.json")


def setup_logging(name: str, debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%m-%d-%y %H:%M:%S", log_colors={"DEBUG": "gray", "INFO": "white", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "red"}, reset=False))
    handler.setLevel(level)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    for _, item in logging.root.manager.loggerDict.items():
        if isinstance(item, logging.Logger):
            item.addHandler(handler)

    return logger
