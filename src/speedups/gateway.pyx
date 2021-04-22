import asyncio
import logging
import time

log = logging.getLogger(__name__)

cdef class GatewayRatelimiter:
    cdef public int max
    cdef public int remaining
    cdef public float window
    cdef public float per
    cdef public object lock
    cdef public object shard_id

    def __init__(self, count: int = 110, per: float = 60.0):
        # The default is 110 to give room for at least 10 heartbeats per minute
        self.max = count
        self.remaining = count
        self.window = 0.0
        self.per = per
        self.lock = asyncio.Lock()
        self.shard_id = None

    cpdef bint is_ratelimited(self):
        cdef float current = time.time()

        if current > self.window + self.per:
            return False

        return self.remaining == 0

    cpdef float get_delay(self):
        cdef float current = time.time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        if self.remaining == 0:
            self.window = current

        return 0.0

    async def block(self):
        async with self.lock:
            delta = self.get_delay()

            if delta:
                log.warning('WebSocket in shard ID %s is ratelimited, waiting %.2f seconds', self.shard_id, delta)
                await asyncio.sleep(delta)
