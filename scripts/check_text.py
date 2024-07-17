# ruff: noqa: T201

import json
import os
import re
import sys
from collections import Counter
from typing import Any

from common.utils.setup import load_data

DEFAULT_TRANSLATION = "en"
FORMAT_BRACES_REGEX = re.compile(r"\{[^}]*\}", re.RegexFlag.MULTILINE)


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

    if isinstance(obj, str):
        obj_matches = Counter(FORMAT_BRACES_REGEX.findall(obj))
        against_matches = Counter(FORMAT_BRACES_REGEX.findall(against))
        matches_diff = {
            k: obj_matches.get(k, 0) - against_matches.get(k, 0)
            for k in set(obj_matches.keys()) | set(against_matches.keys())
        }

        formatted_diff = ", ".join([
            f"{key}.{diff:+}" for key, diff in matches_diff.items() if diff
        ])

        if obj_matches != against_matches:
            print(
                f"MISMATCHED FORMAT VARIABLES ({against_name}): {'.'.join(map(str, keys))} "
                f"=> {formatted_diff}"
            )

    return error


def run():
    with open(f"bot/data/text/{DEFAULT_TRANSLATION}.json", "r", encoding="utf8") as f:
        en_data = json.load(f)[DEFAULT_TRANSLATION]

    data_file = load_data()

    error = False

    for filename in os.listdir("bot/data/text"):
        lang = filename.removesuffix(".json")
        if lang == DEFAULT_TRANSLATION:
            continue

        if lang in data_file.disabled_translations:
            continue

        with open(f"bot/data/text/{filename}", "r", encoding="utf8") as f:
            data = json.load(f)[lang]

        error |= check_obj([lang], en_data, data, lang)

    if error:
        sys.exit(1)


if __name__ == "__main__":
    run()
