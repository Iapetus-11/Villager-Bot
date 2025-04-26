from pydantic import BaseModel


class Item(BaseModel):
    name: str
    sell_price: int
    amount: int
    sticky: bool
    sellable: bool
