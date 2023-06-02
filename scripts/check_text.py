import json
import os
from typing import Any


def check_obj(keys: list[Any], obj: Any, against: Any, against_name: str):
    if isinstance(obj, list):
        obj = dict(enumerate(obj))

        if isinstance(against, list):
            against = dict(enumerate(against))

    if isinstance(obj, dict):
        # check each obj in the dict against against
        for key, value in obj.items():
            if key not in against:
                print(f"MISSING KEY ({against_name}): {'.'.join(map(str, keys))}.{key}")
                continue

            check_obj(keys + [key], value, against[key], against_name)

        # check to see if against has any keys that obj doesn't have
        if isinstance(against, dict):
            if key_diff := (set(against.keys()) - set(obj.keys())):
                print(
                    f"EXTRA KEYS ({against_name}): {'.'.join(map(str, keys))}.[{','.join(map(str, key_diff))}]"
                )


def run():
    with open("bot/data/text/en.json", "r", encoding="utf8") as f:
        en_data = json.load(f)["en"]

    with open("bot/secrets.json", "r") as f:
        secrets = json.load(f)

    disabled_translations = secrets.get("disabled_translations", [])

    for filename in os.listdir("bot/data/text"):
        with open(f"bot/data/text/{filename}", "r", encoding="utf8") as f:
            lang = filename.replace(".json", "")
            data = json.load(f)[lang]

            if lang in disabled_translations:
                continue

            check_obj([lang], en_data, data, lang)


if __name__ == "__main__":
    run()
