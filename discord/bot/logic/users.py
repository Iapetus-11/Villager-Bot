from bot.models.db.item import Item
from bot.models.db.user import User


def calc_total_wealth(db_user: User, items: list[Item]):
    return (
        db_user.emeralds
        + db_user.vault_balance * 9
        + sum(u_it.sell_price * u_it.amount for u_it in items if u_it.sell_price > 0)
    )
