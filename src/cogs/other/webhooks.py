from discord.ext import commands
from aiohttp import web
import traceback
import asyncio
import discord
import arrow

import util.cj as cj


class Webhooks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.k = bot.k

        self.db = bot.get_cog("Database")

        self.server_runner = None
        self.webhook_server = None

        self.webhooks_task = bot.loop.create_task(self.webhooks_setup())
        self.stats_task = bot.loop.create_task(self.update_stats())

        self.lock = asyncio.Lock()

    def cog_unload(self):
        self.bot.loop.create_task(self.server_runner.cleanup())
        self.bot.loop.create_task(self.webhook_server.close())

        self.webhooks_task.cancel()
        self.stats_task.cancel()

    async def update_stats(self):
        await self.bot.wait_until_ready()

        while True:
            try:
                await self.bot.aiohttp.post(
                    f"https://top.gg/api/bots/{self.bot.user.id}/stats",
                    headers={"Authorization": self.k.topgg_api},
                    json={"server_count": str(len(self.bot.guilds))},
                )
            except Exception as e:
                self.bot.logger.error(e)

            await asyncio.sleep(3600)

    async def webhooks_setup(self):  # holy fucking shit that's hot
        async def handler(req):
            try:
                if req.headers.get("Authorization") == self.k.topgg_webhook:
                    self.bot.dispatch("topgg_event", cj.classify(await req.json()))
                else:
                    return web.Response(status=401)
            finally:
                return web.Response()

        app = web.Application()

        app.router.add_post(self.d.hookspath, handler)

        self.server_runner = web.AppRunner(app)
        await self.server_runner.setup()

        self.webhook_server = web.TCPSite(self.server_runner, "0.0.0.0", self.d.hooksport)
        await self.webhook_server.start()

    async def reward(self, user_id, amount, streak=None):
        user = self.bot.get_user(user_id)
        user_str = "an unknown user" if user is None else discord.utils.escape_markdown(user.display_name)

        await self.bot.get_channel(self.d.vote_channel_id).send(f":tada::tada: **{user_str}** has voted! :tada::tada:")

        if user is not None:
            try:
                if streak is None:
                    await self.db.balance_add(user_id, amount)
                    await self.bot.send(user, f"Thanks for voting! You've received **{amount}**{self.d.emojis.emerald}!")
                elif streak % 16 == 0:
                    barrels = int(streak // 32 + 1)
                    await self.db.add_item(user.id, "Barrel", 1024, barrels)
                    await self.bot.send(user, f"Thanks for voting! You've received {barrels}x **Barrel**!")
                else:
                    await self.db.balance_add(user_id, amount)
                    await self.bot.send(
                        user,
                        f"Thanks for voting! You've received **{amount}**{self.d.emojis.emerald}! (Vote streak is now {streak})",
                    )
            except BaseException as e:
                traceback_text = "".join(traceback.format_exception(type(e), e, e.__traceback__, 4))
                await self.bot.send(
                    self.bot.get_channel(self.d.error_channel_id), f"Voting error: {user} ```{traceback_text}```"
                )

    @commands.Cog.listener()
    async def on_topgg_event(self, data):
        if data.type != "upvote":
            self.bot.logger.info("\u001b[35m top.gg webhooks test\u001b[0m")
            await self.bot.get_channel(self.d.error_channel_id).send("TOP.GG WEBHOOKS TEST")
            return

        uid = int(data.user)

        async with self.lock:
            db_user = await self.db.fetch_user(uid)

            streak_time = db_user["streak_time"]
            vote_streak = db_user["vote_streak"]

            if streak_time is None:  # time
                streak_time = 0

            if arrow.get(streak_time) > arrow.utcnow().shift(hours=-12):
                return

            self.bot.logger.info(f"\u001b[32;1m{uid} voted on top.gg\u001b[0m")
            self.d.votes_topgg += 1

            amount = self.d.topgg_reward

            if data.isWeekend:
                amount *= 2

            amount *= len(self.d.mining.pickaxes) - self.d.mining.pickaxes.index(await self.db.fetch_pickaxe(uid))

            if vote_streak is None or vote_streak == 0:
                vote_streak = 0

            vote_streak += 1

            if arrow.utcnow().shift(days=-1, hours=-12) > arrow.get(streak_time):  # vote expired
                vote_streak = 1

            amount *= 5 if vote_streak > 5 else vote_streak

            await self.db.update_user(uid, "streak_time", arrow.utcnow().timestamp())
            await self.db.update_user(uid, "vote_streak", vote_streak)

        await self.reward(uid, amount, vote_streak)


def setup(bot):
    bot.add_cog(Webhooks(bot))
