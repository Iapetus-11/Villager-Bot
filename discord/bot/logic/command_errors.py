from datetime import datetime, timedelta, timezone
from typing import Any

from discord.ext.commands import CommandError


class CommandOnKarenCooldown(CommandError):
    def __init__(self, cooldown_until: datetime):
        self.cooldown_until = cooldown_until
        super().__init__(f"You are on cooldown. Try again in {self.remaining.total_seconds():.2f}s")

    @property
    def remaining(self) -> timedelta:
        return self.cooldown_until - datetime.now(timezone.utc)


class UserBotBanned(CommandError):
    def __init__(self):
        super().__init__("You are banned from this bot")


class BotNotReadyYet(CommandError):
    def __init__(self):
        super().__init__("Bot has not finished starting yet")


class CommandDisabledByGuild(CommandError):
    def __init__(self) -> None:
        super().__init__("Command is disabled by this Discord server")