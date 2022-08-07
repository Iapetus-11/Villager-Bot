import logging
from typing import Awaitable, Callable, Optional

from aiohttp import web
from pydantic import BaseModel, ValidationError

from karen.models.secrets import TopggWebhookSecrets


class TopggVote(BaseModel):
    bot: int
    user: int
    type: str
    isWeekend: bool
    query: Optional[str]


class VotingWebhookServer:
    def __init__(
        self,
        secrets: TopggWebhookSecrets,
        callback: Callable[[TopggVote], Awaitable[None]],
        logger: logging.Logger,
    ):
        self.secrets = secrets
        self.callback = callback
        self.logger = logger.getChild("voting")

        self._runner: Optional[web.AppRunner] = None
        self._server: Optional[web.TCPSite] = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_post(self.secrets.path, self._handle_post)

        runner = self._runner = web.AppRunner(app)
        await runner.setup()

        server = self._server = web.TCPSite(
            runner, self.secrets.host, self.secrets.port, shutdown_timeout=1
        )
        await server.start()

        self.logger.info(
            "Started voting webhooks server on %s:%s", self.secrets.host, self.secrets.port
        )

    async def stop(self) -> None:
        if self._server is not None:
            await self._server.stop()

        if self._runner is not None:
            await self._runner.cleanup()
            
        self.logger.info("Stopped voting webhooks server")

    async def _handle_post(self, request: web.Request) -> web.Response:
        auth_header = request.headers.get("Authorization")

        if auth_header != self.secrets.auth:
            self.logger.error("Invalid authorization header received from top.gg: %s", auth_header)
            return web.Response(status=401)

        try:
            data = TopggVote(**await request.json())
        except ValidationError:
            self.logger.error("Invalid data received from top.gg", exc_info=True)
            return web.Response(status=400)

        self.logger.info("Calling handler for vote from top.gg for user %s", data.user)
        await self.callback(data)

        return web.Response(status=200)
