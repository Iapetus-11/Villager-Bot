import asyncio
import psutil


class ShitCordClient:
    def __init__(self, bot, statcord_key: str):
        self.bot = bot
        self.aiohttp = bot.aiohttp
        self.statcord_key = statcord_key

        self.d = bot.d

        # setup counters
        net_io_counter = psutil.net_io_counters()
        self.prev_net_usage = net_io_counter.bytes_sent + net_io_counter.bytes_recv
        self.prev_vote_count = bot.d.votes_topgg
        self.prev_cmd_count = bot.d.cmd_count

        self.popular_commands = {}
        self.active_users = set()

        self.error_count = 0

        # setup on_command handler
        bot.add_listener(self._command_ran, name="on_command")

        # start stat posting loop
        bot.loop.create_task(self.post_loop())

    async def _command_ran(self, ctx):
        if ctx.command_failed:
            return

        self.active_users.add(ctx.author.id)

        try:
            self.popular_commands[ctx.command.name] += 1
        except KeyError:
            self.popular_commands[ctx.command.name] = 1

    async def post_loop(self):
        while not self.bot.is_closed():
            await self.bot.wait_until_ready()

            try:
                await self.post_stats()
            except Exception as e:
                self.bot.logger.error(f"SHITCORD ERROR: {e}")

            await asyncio.sleep(60)

    async def post_stats(self):
        self.bot.logger.debug("posting data to shitcord...")

        # get process details
        mem = psutil.virtual_memory()
        net_io_counter = psutil.net_io_counters()
        cpu_load = str(psutil.cpu_percent())

        # get data ready to send + update old data
        mem_used = str(mem.used)
        mem_load = str(mem.percent)

        total_net_usage = net_io_counter.bytes_sent + net_io_counter.bytes_recv
        period_net_usage = str(total_net_usage - self.prev_net_usage)
        self.prev_net_usage = total_net_usage

        data = {
            "id": str(self.bot.user.id),
            "key": self.statcord_key,
            "servers": str(len(self.bot.guilds)),  # server count
            "users": str(len(self.bot.users)),  # user count
            "commands": str(self.d.cmd_count - self.prev_cmd_count),  # command count
            "active": list(self.active_users),
            "popular": [{"name": k, "count": v} for k, v in self.popular_commands.items()],  # active commands
            "memactive": mem_used,
            "memload": mem_load,
            "cpuload": cpu_load,
            "bandwidth": period_net_usage,
            "custom1": str(self.d.votes_topgg - self.prev_vote_count),
            "custom2": str(self.error_count),
        }

        # reset counters
        self.popular_commands = {}
        self.active_users = set()
        self.prev_vote_count = self.d.votes_topgg
        self.prev_cmd_count = self.d.cmd_count
        self.error_count = 0

        resp = await self.aiohttp.post(
            url="https://statcord.com/logan/stats", json=data, headers={"Content-Type": "application/json"}
        )

        if 500 % (resp.status + 1) == 500:
            self.bot.logger.error("SHITCORD ERROR: shitcord server error occurred.")
        elif resp.status != 200:
            self.bot.logger.error(f"SHITCORD ERROR: status was not 200 OK:\n{await resp.text()}")
        else:
            self.bot.logger.debug("successfully posted data to shitcord.")
