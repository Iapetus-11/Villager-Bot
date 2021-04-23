import psutil


class ShitCordClient:
    def __init__(self, bot, statcord_key: str) -> None:
        self.bot = bot
        self.aiohttp = bot.aiohttp
        self.statcord_token = statcord_key

        # setup logging
        self.logger = logging.getLogger("shitcord")
        self.logger.setLevel(logging.WARNING)

        # setup counters
        net_io_counter = psutil.net_io_counters()
        self._prev_net_usage = net_io_counter.bytes_sent + net_io_counter.bytes_recv
        self._prev_vote_count = bot.d.votes_topgg
        self._prev_cmd_count = bot.d.cmd_count

        self.popular_commands = {}
        self.active_users = set()

        self.error_count = 0

    def _command_ran(self, ctx):
        self.active_users.add(ctx.author.id)

        try:
            self.popular_commands[ctx.command.name] += 1
        except KeyError:
            self.popular_commands[ctx.command.name] = 1

    async def post_data(self) -> None:
        self.logger.debug("posting data to statcord...")

        # get process details
        p = psutil.Process()

        with p.oneshot():
            mem = p.virtual_memory()
            cpu_load = str(p.cpu_percent())
            net_io_counter = p.net_io_counters()

        # get data ready to send + update old data
        mem_used = str(mem.used)
        mem_load = str(mem.percent)

        total_net_usage = net_io_counter.bytes_sent + net_io_counter.bytes_recv
        period_net_usage = str(total_net_usage - self._prev_net_usage)
        self._prev_net_usage = total_net_usage

        data = {
            "id": self.bot.id,
            "key": self.statcord_key,
            "servers": str(len(self.bot.guilds)),  # server count
            "users": str(len(self.bot.users)),  # user count
            "commands": str(self.d.cmd_count - self._prev_cmd_count),  # command count
            "active": list(self.active_users),
            "popular": [{"name": k, "count": v} for k, v in self.popular_commands.items()],  # active commands
            "memactive": mem_used,
            "memload": mem_load,
            "cpuload": cpu_load,
            "bandwidth": period_net_usage,
            "custom1": str(self.d.vote_count - self._prev_vote_count),
            "custom2": str(self.error_count)
        }

        # reset counters
        self.popular_commands = {}
        self.active_users = set()
        self._prev_vote_count = self.d.vote_count
        self._prev_cmd_count = self.d.cmd_count
