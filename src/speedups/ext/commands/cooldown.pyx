import time

cdef class Cooldown:
    cdef signed long long rate
    cdef double per
    cdef double _window
    cdef signed long long _tokens
    cdef double _last

    def __init__(self, signed long long rate, double per):
        self.rate = rate
        self.per = per
        self._window = 0.0
        self._tokens = rate
        self._last = 0.0

    cpdef signed long long get_tokens(self, double current = 0.0):
        if not current:
            current = time.time()

        cdef signed long long tokens = self._tokens

        if current > self._window + self.per:
            tokens = self.rate

        return tokens

    cpdef double get_retry_after(self, double current = 0.0):
        current = current or time.time()
        cdef signed long long tokens = self.get_tokens(current)

        if tokens == 0:
            return self.per - (current - self._window)

        return 0.0

    cpdef double update_rate_limit(self, double current = 0.0):
        current = current or time.time()
        self._last = current

        self._tokens = self.get_tokens(current)

        if self._tokens == self.rate:
            return self.per - (current - self._window)

        self._tokens -= 1

        if self._tokens == 0:
            self._window = current

    cpdef void reset(self):
        self._tokens = self.rate
        self._last = 0.0

    cpdef Cooldown copy(self):
        return Cooldown(self.rate, self.per)

    def __repr__(self):
        return f"<Cooldown rate: {self.rate} per: {self.per} window: {self._window} tokens: {self._tokens}>"
