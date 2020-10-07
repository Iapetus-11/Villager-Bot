from aiohttp import web
import classyjson as cj
import aiohttp
import asyncio


class BotLists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.ses = aiohttp.ClientSession()
        self.webhook_server = None

        self.bot.loop.create_task(webhooks_setup())

    async def webhooks_setup(self):
        async def handler(req):
            if req.headers.get('Authorization') == self.d.disbots_auth:
                self.bot.dispatch('disbots_event', cj.classify(await req.json()))
            elif req.headers.get('Authorization') == self.d.topgg_hooks_auth:
                self.bot.dispatch('topgg_event', cj.classify(await req.json()))
            else:
                return web.Response(status=401)

            return web.Response()

        app = aiohttp.web.Application()

        app.router.add_post(self.d.hookspath, handler)

        runner = aiohttp.web.AppRunner(app)
        await runner.setup()

        self.webhook_server = aiohttp.web.TCPSite(runner, '0.0.0.0', self.d.hooksport)

    @commands.Cog.listener()
    async def on_disbots_event(self, data):
        if data.type != 'like':
            await self.bot.get_channel(self.d.error_channel_id).send('DISBOTS.GG WEBHOOKS TEST')

    @commands.Cog.listener()
    async def on_topgg_event(self, data):
        pass
