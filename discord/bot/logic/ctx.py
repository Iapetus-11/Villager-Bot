from __future__ import annotations

import typing
import discord
from discord.ext.commands import Context

from bot.models.translation import Translation

if typing.TYPE_CHECKING:
    from bot.villager_bot import VillagerBotCluster


class CustomContext(Context["VillagerBotCluster"]):
    """Custom context class to provide extra helper methods and multi-language support"""

    embed_color: discord.Color | None  # used in send_embed(...) and reply_embed(...)
    l: Translation  # the translation of the bot text for the current context  # noqa: E741
    failure_reason: str | None  # failure reason used in some command error handling
    custom_error: Exception | None

    def __init__(self, *args, embed_color: discord.Color | None = None, **kwargs):
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


def get_user_and_lang_from_loc(
    langs: dict[str, Translation],
    loc: CustomContext | Context[VillagerBotCluster] | discord.User,
) -> tuple[int, Translation]:
    user_id: int
    if isinstance(loc, CustomContext | Context):
        user_id = loc.author.id
    else:
        user_id = loc.id

    lang = langs["en"]
    if isinstance(loc, CustomContext | Context) and hasattr(loc, "l"):
        lang = loc.l

    return user_id, lang
