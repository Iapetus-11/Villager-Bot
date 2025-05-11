import datetime


class CommandOnKarenCooldownError(Exception):
    def __init__(self, cooldown_until: datetime.datetime):
        self.cooldown_until = cooldown_until
