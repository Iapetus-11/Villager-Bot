from pydantic import BaseModel


class Cooldown(BaseModel):
    can_run: bool
    remaining: float | None
