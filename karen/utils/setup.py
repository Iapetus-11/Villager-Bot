import logging

from karen.models.secrets import Secrets


def setup_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="[Karen] %(levelname)s: %(message)s")
    return logging.getLogger("karen")


def load_secrets() -> Secrets:
    return Secrets.parse_file("karen/secrets.json")
