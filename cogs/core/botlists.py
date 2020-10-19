from discord.ext import commands
from aiohttp import web
import classyjson as cj
import aiohttp  # aiohttp makes me hard
import asyncio


class BotLists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

        self.ses = aiohttp.ClientSession()
        self.webhook_server = None

        self.bot.loop.create_task(self.webhooks_setup())
        self.bot.loop.create_task(self.update_stats())

    async def update_stats(self):
        await self.bot.wait_until_ready()

        while True:
            try:
                await self.ses.post(
                    f'https://top.gg/api/bots/{self.bot.user.id}/stats',
                    headers={'Authorization': self.d.topgg_post_auth},
                    json={'server_count': str(len(self.bot.guilds))}
                )
            except Exception as e:
                self.bot.logger.error(e)

            await asyncio.sleep(3600)

    async def webhooks_setup(self):  # holy fucking shit that's hot
        async def handler(req):
            if req.headers.get('Authorization') == self.d.topgg_hooks_auth:
                self.bot.dispatch('topgg_event', cj.classify(await req.json()))
            else:
                return web.Response(status=401)

            return web.Response()

        app = web.Application()

        app.router.add_post(self.d.hookspath, handler)

        runner = web.AppRunner(app)
        await runner.setup()

        self.webhook_server = web.TCPSite(runner, '0.0.0.0', self.d.hooksport)
        await self.webhook_server.start()

    async def reward(user_id, amount):
        await self.db.balance_add(user_id, amount)

        user = self.bot.get_user(user_id)
        user_str = 'an unknown user' if user is None else discord.utils.escape_markdown(user.display_name)

        await self.bot.get_channel(self.d.vote_channel_id).send(f':tada::tada: **{user_str}** has voted! :tada::tada:')

        if user is not None:
            try:
                await user.send(f'Thanks for voting! You\'ve received **{amount}**{self.d.emojis.emerald}!')
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_topgg_event(self, data):
        if data.type != 'upvote':
            self.bot.logger.info('\u001b[35m top.gg webhooks test\u001b[0m')
            await self.bot.get_channel(self.d.error_channel_id).send('TOP.GG WEBHOOKS TEST')
            return

        self.bot.logger.info(f'\u001b[32;1m{data.user} voted on top.gg\u001b[0m DEBUG/TESTING: {data}')

        amount = self.d.topgg_reward * self.d.base_multi * (self.d.weekend_multi * data.isWeekend)
        amount *= len(self.d.mining.pickaxes) - self.d.mining.pickaxes.index(self.d.mining.pickaxes[await self.db.fetch_pickaxe(data.user)])

        await self.reward(data.user, amount)


def setup(bot):
    bot.add_cog(BotLists(bot))
