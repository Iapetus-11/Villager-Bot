import discord
from discord.ext.commands import Context

from bot.models.translation import Translation


class CustomContext(Context):
    """Custom context class to provide extra helper methods and multi-language support"""

    embed_color: discord.Color  # used in send_embed(...) and reply_embed(...)
    l: Translation  # the translation of the bot text for the current context  # noqa: E741
    failure_reason: str | None  # failure reason used in some command error handling
    custom_error: Exception | None

    def __init__(self, *args, embed_color: discord.Color = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.embed_color = embed_color

    async def send_embed(self, message: str, *, ignore_exceptions: bool = False) -> None:
        await self.bot.send_embed(self, message, ignore_exceptions=ignore_exceptions)

    async def reply_embed(
        self,
        message: str,
        ping: bool = False,
        *,
        ignore_exceptions: bool = False,
    ) -> None:
        await self.bot.reply_embed(self, message, ping, ignore_exceptions=ignore_exceptions)

    def __repr__(self) -> str:
        guild_id = getattr(self.guild, "id", None)
        author_id = getattr(self.author, "id", None)

        return f"Ctx({guild_id=}, {author_id=})"


Ctx = CustomContext
