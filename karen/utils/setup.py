import logging


def setup_karen_logging():
    logger = logging.getLogger("KAREN")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[Karen] %(levelname)s: %(message)s"))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
