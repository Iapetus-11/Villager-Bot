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

        self.bot.loop.create_task(webhook_setup())

    async def webhook_setup(self):
        async def handler(req):
            if req.headers.get('Authorization') == self.d.disbots_auth:
                self.bot.dispatch('disbots_event')
            elif req.headers.get('Authorization') == self.d.topgg_hooks_auth:
                self.bot.dispatch('topgg_event')
            else:
                return web.Response(status=401)

            return web.Response()

        app = aiohttp.web.Application()

        app.router.add_post('/votehook', handler)

        runner = aiohttp.web.AppRunner(app)
        await runner.setup()

        self.webhook_server = aiohttp.web.TCPSite(runner, '0.0.0.0', 5000)
