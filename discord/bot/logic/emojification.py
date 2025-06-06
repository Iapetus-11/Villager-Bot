from typing import Any

from bot.utils.default_sentinel import DEFAULT_SENTINEL


def emojify_item(d, item: str, default: Any = DEFAULT_SENTINEL) -> str | Any:
    try:
        emoji_key = d.emoji_items[item.lower()]

        if emoji_key.startswith("fish."):
            return d.emojis.fish[emoji_key[5:]]

        if emoji_key.startswith("farming.normal."):
            return d.emojis.farming.normal[emoji_key[15:]]

        if emoji_key.startswith("farming.seeds."):
            return d.emojis.farming.seeds[emoji_key[14:]]

        return d.emojis[emoji_key]
    except KeyError:
        return d.emojis.air if default is DEFAULT_SENTINEL else default


def emojify_crop(d, crop: str):
    return d.emojis.farming.growing[d.farming.emojis.growing[crop]]
