from bot.models.data import Data
from bot.services.karen.resources.commands.shop import ShopItemEntry


def format_required_items(d: Data, shop_item: ShopItemEntry, amount: int = 1):
    base = f" {shop_item.buy_price * amount}{d.emojis.emerald}"

    if not (shop_item.requires and shop_item.requires.items):
        return base

    for req_item, req_amount in shop_item.requires.items.items():
        base += f" + {req_amount * amount}{d.emojis[d.emoji_items[req_item]]}"

    return base
