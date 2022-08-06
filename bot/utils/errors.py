class CommandOnKarenCooldown(Exception):
    def __init__(self, remaining: float):
        self.remaining = remaining


class MaxKarenConcurrencyReached(Exception):
    pass
