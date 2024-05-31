import time
from collections import defaultdict


class MaxConcurrencyManager:
    def __init__(self):
        self.limits = set[tuple[str, int]]()

    def acquire(self, command: str, user_id: int) -> None:
        self.limits.add((command, user_id))

    def release(self, command: str, user_id: int) -> None:
        try:
            self.limits.remove((command, user_id))
        except KeyError:
            pass

    def check(self, command: str, user_id: int) -> bool:
        return (command, user_id) not in self.limits


class CooldownManager:
    def __init__(self, cooldown_rates: dict[str, float]):
        self.rates = cooldown_rates  # {command_name: seconds_per_command}

        # {command_name: {user_id: time.time()}}
        self._cooldowns = defaultdict[str, dict[int, float]](dict)

    def add_cooldown(self, command: str, user_id: int) -> None:
        self._cooldowns[command][user_id] = time.time()

    def clear_cooldown(self, command: str, user_id: int) -> None:
        self._cooldowns[command].pop(user_id, None)

    def get_remaining(self, command: str, user_id: int) -> float:  # returns remaning cooldown or 0
        started = self._cooldowns[command].get(user_id, 0)
        remaining = self.rates[command] - (time.time() - started)

        if remaining < 0.01:
            self.clear_cooldown(command, user_id)
            return 0

        return remaining

    def check_add_cooldown(self, command: str, user_id: int) -> tuple[bool, float | None]:
        remaining = self.get_remaining(command, user_id)

        if remaining:
            return False, remaining

        self.add_cooldown(command, user_id)

        return True, None

    def clear_dead(self) -> None:
        for command, users in list(self._cooldowns.items()):
            for user_id in list(users.keys()):
                if (
                    self.rates[command] - (time.time() - self._cooldowns[command].get(user_id, 0))
                    <= 0
                ):
                    del self._cooldowns[command][user_id]
