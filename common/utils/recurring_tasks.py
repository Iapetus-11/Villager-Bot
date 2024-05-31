import asyncio
import logging
from typing import Awaitable, Callable, Generator, TypeAlias

T_LOOP_CALLABLE: TypeAlias = Callable[[], Awaitable[None]]


class RecurringTask:
    """Helper class for creating recurring tasks / async loops"""

    __slots__ = ("loop_callable", "interval", "sleep_first", "_logger", "name", "_loop_task")

    def __init__(
        self,
        loop_callable: T_LOOP_CALLABLE,
        interval: float,
        sleep_first: bool,
    ):
        self.loop_callable = loop_callable
        self.interval = interval
        self.sleep_first = sleep_first

        self.name = loop_callable.__qualname__

        self._logger: logging.Logger | None = None

        self._loop_task: asyncio.Task | None = None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            raise RuntimeError("Logger instance was not set")

        return self._logger

    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        self._logger = value

    async def _call(self) -> None:
        self.logger.debug("Calling loop callable: %s", self.name)

        try:
            await self.loop_callable()
        except Exception:
            self.logger.exception(
                "An error ocurred while calling the loop callable: %s",
                self.name,
            )

    async def _loop(self) -> None:
        if self.sleep_first:
            await asyncio.sleep(self.interval)

        while True:
            asyncio.create_task(self._call())
            await asyncio.sleep(self.interval)

    def start(self):
        if self._loop_task is not None:
            raise RuntimeError("This loop has already been started")

        self.logger.info("Started recurring task: %s", self.name)

        self._loop_task = asyncio.create_task(self._loop())

    def cancel(self):
        if self._loop_task is not None:
            self._loop_task.cancel()
            self._loop_task = None

        self.logger.info("Cancelled recurring task: %s", self.name)


def recurring_task(
    *,
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    sleep_first: bool = True,
):
    """Decorator for creating a RecurringTask"""

    def _recurring_task(loop_callable: T_LOOP_CALLABLE):
        return RecurringTask(loop_callable, seconds + 60 * minutes + 3600 * hours, sleep_first)

    return _recurring_task


class RecurringTasksMixin:
    """Adds support for recurring tasks in the subclass."""

    def __init__(self, logger: logging.Logger):
        for rc in self.__get_recurring_tasks():
            # bind coro funcs to their class instance
            rc.loop_callable = rc.loop_callable.__get__(self)

            rc.logger = logger

    def __get_recurring_tasks(self) -> Generator[RecurringTask, None, None]:
        for obj_name in dir(self):
            try:
                obj = getattr(self, obj_name)
            except Exception:
                continue

            if isinstance(obj, RecurringTask):
                yield obj

    def start_recurring_tasks(self) -> None:
        for rc in self.__get_recurring_tasks():
            rc.start()

    def cancel_recurring_tasks(self) -> None:
        for rc in self.__get_recurring_tasks():
            rc.cancel()
