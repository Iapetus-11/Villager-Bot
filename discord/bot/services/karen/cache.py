from datetime import datetime, timedelta, timezone
import typing


class CacheableResource[T, TId](typing.Protocol):
    async def get(self, id_: TId) -> T: ...


class KarenResourceCache[T, TId]:
    _resource: CacheableResource[T, TId]
    _cache: dict[TId, tuple[datetime, T]]
    _exipre_after: timedelta

    def __init__(self, resource: CacheableResource[T, TId], *, expire_after: timedelta):
        self._resource = resource
        self._cache = {}
        self._expire_after = expire_after

    async def get(self, id_: TId) -> T:
        if id_ in self._cache:
            return self._cache[id_][1]

        obj = await self._resource.get(id_)
        self._cache[id_] = (datetime.now(timezone.utc), obj)

        return obj

    def prune(self) -> None:
        for key, (entry_time, _) in list(self._cache.items()):
            if (datetime.now(timezone.utc) - entry_time) > self._expire_after:
                self._cache.pop(key, None)
