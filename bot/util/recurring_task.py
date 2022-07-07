import asyncio
import inspect
import logging
from typing import Callable, Coroutine, Optional

from util.code import format_exception


class RecurringTask:
    """Helper class for creating recurring tasks / async loops"""

    __slots__ = ("coro_func", "interval", "logger", "sleep_first", "_loop_task")

    def __init__(
        self,
        coro_func: Callable[[], Coroutine],
        interval: int,
        logger: logging.Logger,
        sleep_first: bool,
    ):
        self.coro_func = coro_func
        self.interval = interval
        self.logger = logger
        self.sleep_first = sleep_first

        self._loop_task: asyncio.Task = None

    async def _call(self) -> None:
        try:
            await self.coro_func()
        except Exception as e:
            self.logger.error(format_exception(e))

    async def _loop(self) -> None:
        if self.sleep_first:
            await asyncio.sleep(self.interval)

        while True:
            asyncio.create_task(self._call())
            await asyncio.sleep(self.interval)

    def start(self):
        self._loop_task = asyncio.create_task(self._loop())

    def cancel(self):
        self._loop_task.cancel()
        self._loop_task = None


def recurring_task(
    *,
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    logger: Optional[logging.Logger] = None,
    sleep_first: bool = True,
):
    """Decorator for creating a RecurringTask"""

    if logger is None:
        logger = logging.getLogger(inspect.currentframe().f_back.f_code.co_name)

    def _recurring_task(coro_func: Callable[[], Coroutine]):
        return RecurringTask(coro_func, seconds + 60 * minutes + 3600 * hours, logger, sleep_first)

    return _recurring_task


class RecurringTasksMixin:
    """Adds support for recurring tasks in the subclass."""

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)

        # bind functions to their class manually
        for obj_name in dir(cls):  # for some reason vars() doesn't get stuff from __slots__?
            obj = getattr(cls, obj_name)

            if isinstance(obj, RecurringTask):
                obj.coro_func = obj.coro_func.__get__(self)

        return self
