# ruff: noqa: T201

import json
import os
import sys
from typing import Any

from common.utils.setup import load_data


def check_obj(keys: list[Any], obj: Any, against: Any, against_name: str) -> bool:
    error = False

    if isinstance(obj, list):
        obj = dict(enumerate(obj))

        if isinstance(against, list):
            against = dict(enumerate(against))

    if isinstance(obj, dict):
        # check each obj in the dict against against
        for key, value in obj.items():
            if key not in against:
                print(f"MISSING KEY ({against_name}): {'.'.join(map(str, keys))}.{key}")
                error = True
                continue

            error |= check_obj(keys + [key], value, against[key], against_name)

        # check to see if against has any keys that obj doesn't have
        if isinstance(against, dict) and (key_diff := (set(against.keys()) - set(obj.keys()))):
            print(
                f"EXTRA KEYS ({against_name}): {'.'.join(map(str, keys))}"
                f".[{','.join(map(str, key_diff))}]",
            )
            error = True

    return error


def run():
    with open("bot/data/text/en.json", "r", encoding="utf8") as f:
        en_data = json.load(f)["en"]

    data_file = load_data()

    error = False

    for filename in os.listdir("bot/data/text"):
        with open(f"bot/data/text/{filename}", "r", encoding="utf8") as f:
            lang = filename.replace(".json", "")
            data = json.load(f)[lang]

            if lang in data_file.disabled_translations:
                continue

            error |= check_obj([lang], en_data, data, lang)

    if error:
        sys.exit(1)


if __name__ == "__main__":
    run()
