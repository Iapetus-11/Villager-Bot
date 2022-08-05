from typing import Optional

from pydantic import BaseModel


class Cooldown(BaseModel):
    can_run: bool
    remaining: Optional[float]
