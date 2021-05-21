from discord.ext import commands
from discord.ext.commands import BucketType
import asyncio
import time

def create_cdmapping_class(ipc):
    class CooldownMapping:
        def __init__(self, original):
            self._cache = {}
            self._cooldown = original

        def copy(self):
            ret = CooldownMapping(self._cooldown)
            ret._cache = self._cache.copy()
            return ret

        @property
        def valid(self):
            return self._cooldown is not None

        @classmethod
        def from_cooldown(cls, rate, per, type):
            return cls(Cooldown(rate, per, type))

        def _bucket_key(self, msg):
            return self._cooldown.type(msg)

        def _verify_cache_integrity(self, current=None):
            # we want to delete all cache objects that haven't been used
            # in a cooldown window. e.g. if we have a  command that has a
            # cooldown of 60s and it has not been used in 60s then that key should be deleted
            current = current or time.time()
            dead_keys = [k for k, v in self._cache.items() if current > v._last + v.per]
            for k in dead_keys:
                del self._cache[k]

        def get_bucket(self, message, current=None):
            if self._cooldown.type is BucketType.default:
                return self._cooldown

            self._verify_cache_integrity(current)
            key = self._bucket_key(message)
            if key not in self._cache:
                bucket = self._cooldown.copy()
                self._cache[key] = bucket
            else:
                bucket = self._cache[key]

            if bucket.get_retry_after() > 2:
                asyncio.create_task(ipc.broadcast({"type": "update-cooldown", "key": }))

            return bucket

        def update_rate_limit(self, message, current=None):
            bucket = self.get_bucket(message, current)
            return bucket.update_rate_limit(current)



    commands.CooldownMapping = CooldownMapping
    commands.core.CooldownMapping = CooldownMapping
