import asyncio
import contextlib
import aiohttp
import psutil
import logging

from discord import Client as DiscordClient
from typing import Optional, Coroutine, Union, List, Dict, Iterable
from discord.ext.commands import Context

# this could be relative, but apparently Python doesn't like it
from statcord import exceptions


class Client:
    """Client for using the statcord API"""

    def __init__(self, bot, token, **kwargs):
        self.logger = logging.getLogger("statcord")
        self.logging_level = kwargs.get("logging_level", logging.WARNING)
        self.logger.setLevel(self.logging_level)

        if not isinstance(bot, DiscordClient):
            raise TypeError(f"Expected class deriving from discord.Client for arg bot not {bot.__class__.__qualname__}")
        if not isinstance(token, str):
            raise TypeError(f"Expected str for arg token not {token.__class__.__qualname__}")

        self.bot: DiscordClient = bot
        self.key: str = token
        self.base: str = "https://statcord.com/logan/"
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(loop=bot.loop)

        self.mem: Optional[bool] = None
        if kwargs.get("mem"):
            if isinstance(kwargs["mem"], bool):
                self.mem = kwargs["mem"]
            else:
                raise TypeError(f"Memory config: expected type bool not {kwargs['mem'].__class__.__qualname__}.")
        else:
            self.mem = True

        self.cpu: Optional[bool] = None
        if kwargs.get("cpu"):
            if isinstance(kwargs["cpu"], bool):
                self.cpu = kwargs["cpu"]
            else:
                raise TypeError(f"CPU config: expected type bool not {kwargs['cpu'].__class__.__qualname__}")
        else:
            self.cpu = True

        self.bandwidth: Optional[bool] = None
        if kwargs.get("bandwidth"):
            if isinstance(kwargs["bandwidth"], bool):
                self.bandwidth = kwargs["bandwidth"]
            else:
                raise TypeError("Bandwidth config: expected type bool")
        else:
            self.bandwidth = True

        self.debug: Optional[bool] = None
        if kwargs.get("debug"):
            if isinstance(kwargs["debug"], bool):
                self.debug = kwargs["debug"]
            else:
                raise TypeError(f"Debug config: expected type bool not {kwargs['debug'].__class__.__qualname__}")
        else:
            self.debug = False

        self.custom1: Optional[Coroutine] = kwargs.get("custom1") or None
        self.custom2: Optional[Coroutine] = kwargs.get("custom2") or None
        self.active: List[int] = []
        self.commands: int = 0
        self.popular: List[Dict[str, Union[str, int]]] = []
        self.previous_bandwidth: int = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

        self.logger.debug("Statcord debug mode enabled")

    @staticmethod
    def __headers() -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    # noinspection SpellCheckingInspection
    async def __handle_response(self, res: aiohttp.ClientResponse) -> dict:
        try:
            msg = await res.json() or {}
        except aiohttp.ContentTypeError:
            msg = await res.text()
        self.logger.debug(f"Handling response ({res!r}): {msg!s}")
        status = res.status
        if status == 200:
            self.logger.debug(f"Code 200 OK")
            return msg
        elif status == 429:
            self.logger.debug(f"Code 429 Too Many Requests: ratelimited for {msg.get('timeleft')}")
            raise exceptions.TooManyRequests(status, msg, int(msg.get("timeleft")))
        else:
            self.logger.debug(f"Code {status}")
            raise exceptions.RequestFailure(status=status, response=msg)

    @property
    def servers(self) -> str:
        return str(len(self.bot.guilds))

    @property
    def _user_counter(self) -> Iterable[int]:
        for g in self.bot.guilds:
            with contextlib.suppress(AttributeError):
                yield g.member_count

    @property
    def users(self) -> str:
        return str(sum(self._user_counter))

    async def post_data(self) -> None:
        self.logger.debug("Got request to post data.")
        bot_id = str(self.bot.user.id)
        commands = str(self.commands)

        if self.mem:
            mem = psutil.virtual_memory()
            mem_used = str(mem.used)
            mem_load = str(mem.percent)
        else:
            mem_used = "0"
            mem_load = "0"

        if self.cpu:
            cpu_load = str(psutil.cpu_percent())
        else:
            cpu_load = "0"

        if self.bandwidth:
            current_bandwidth = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            bandwidth = str(current_bandwidth - self.previous_bandwidth)
            self.previous_bandwidth = current_bandwidth
        else:
            bandwidth = "0"

        if self.custom1:
            # who knows why PyCharm gets annoyed there /shrug
            # noinspection PyCallingNonCallable
            custom1 = str(await self.custom1())
        else:
            custom1 = "0"

        if self.custom2:
            # who knows why PyCharm gets annoyed there /shrug
            # noinspection PyCallingNonCallable
            custom2 = str(await self.custom2())
        else:
            custom2 = "0"

        # noinspection SpellCheckingInspection
        data = {
            "id": bot_id,
            "key": self.key,
            "servers": self.servers,
            "users": self.users,
            "commands": commands,
            "active": self.active,
            "popular": self.popular,
            "memactive": mem_used,
            "memload": mem_load,
            "cpuload": cpu_load,
            "bandwidth": bandwidth,
            "custom1": custom1,
            "custom2": custom2,
        }
        self.logger.debug(f"Posting stats: {data!s}")
        self.active = []
        self.commands = 0
        self.popular = []

        async with self.session.post(url=self.base + "stats", json=data, headers=self.__headers()) as resp:
            await self.__handle_response(resp)

    def start_loop(self) -> None:
        self.bot.loop.create_task(self.__loop())

    def command_run(self, ctx: Context) -> None:
        self.commands += 1
        if ctx.author.id not in self.active:
            self.active.append(ctx.author.id)

        command = ctx.command.name
        self.logger.debug(f"Command {command} has been run by {ctx.author.id}")
        for cmd in filter(lambda x: x["name"] == command, self.popular):
            cmd["count"] = str(int(cmd["count"]) + 1)
            break
        else:
            self.popular.append({"name": command, "count": "1"})

    async def __loop(self) -> None:
        """
        The internal loop used for automatically posting server/guild count stats
        """
        await self.bot.wait_until_ready()
        if self.debug:
            self.logger.debug("Statcord Auto Post has started!")
        while not self.bot.is_closed():
            self.logger.debug("Posting stats...")
            try:
                await self.post_data()
            except Exception as e:
                self.logger.debug("Got error, dispatching error handlers.")
                await self.on_error(e)
            else:
                self.logger.debug("Posted stats successfully.")
            await asyncio.sleep(60)

    async def on_error(self, error: BaseException) -> None:
        self.logger.exception("Statcord posting exception occurred.", exc_info=error)
