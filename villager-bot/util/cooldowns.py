from collections import defaultdict
import asyncio
import time


class CommandOnKarenCooldown(Exception):
    def __init__(self, remaining: float) -> None:
        self.remaining = remaining


class MaxKarenConcurrencyReached(Exception):
    pass


class MaxConcurrencyManager:
    def __init__(self):
        self.limits = set()

    def acquire(self, command: str, user_id: int) -> None:
        self.limits.add((command, user_id))

    def release(self, command: str, user_id: int) -> None:
        self.limits.remove((command, user_id))

    def check(self, command: str, user_id: int) -> None:
        if (command, user_id) in self.limits:
            return False

        self.acquire(command, user_id)

        return True


class CooldownManager:
    def __init__(self, cooldown_rates: dict):
        self.rates = cooldown_rates  # {command_name: seconds_per_command}
        self.cooldowns = defaultdict(dict)  # {command_name: {user_id: time.time()}}

        self._clear_task = None

    def add_cooldown(self, command: str, user_id: int) -> None:
        self.cooldowns[command][user_id] = time.time()

    def clear_cooldown(self, command: str, user_id: int) -> None:
        self.cooldowns[command].pop(user_id, None)

    def get_remaining(self, command: str, user_id: int) -> float:  # returns remaning cooldown or 0
        started = self.cooldowns[command].get(user_id, 0)
        remaining = self.rates[command] - (time.time() - started)

        if remaining < 0.01:
            self.clear_cooldown(command, user_id)
            return 0

        return remaining

    def check(self, command: str, user_id: int) -> dict:  # checks if command is runnable, if so add cooldown
        remaining = self.get_remaining(command, user_id)

        if remaining:
            return {"can_run": False, "remaining": remaining}

        self.add_cooldown(command, user_id)

        return {"can_run": True}

    async def _clear_dead(self):
        try:
            while True:
                for command, users in list(self.cooldowns.items()):
                    for user_id, started in list(users.items()):
                        if self.rates[command] - (time.time() - self.cooldowns[command].get(user_id, 0)) <= 0:
                            del self.cooldowns[command][user_id]

                await asyncio.sleep(20)
        except asyncio.CancelledError:
            return

    def start(self):
        self._clear_task = asyncio.create_task(self._clear_dead())

    def stop(self):
        self._clear_task.cancel()
