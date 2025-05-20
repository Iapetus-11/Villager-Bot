from __future__ import annotations

import dataclasses
import typing

import discord
from discord.ext.commands import Context

from bot.models.translation import Translation
from bot.services.karen.resources.discord.guild import DiscordGuildSettings as KarenDiscordGuild
from bot.services.karen.resources.users import User as KarenUser

if typing.TYPE_CHECKING:
    from bot.villager_bot import VillagerBotCluster


class CustomContext(Context["VillagerBotCluster"]):
    """Custom context class to provide extra helper methods and multi-language support"""

    @dataclasses.dataclass(frozen=True, slots=True, kw_only=True, eq=False, match_args=False)
    class KarenData:
        user: KarenUser
        guild: KarenDiscordGuild | None

    l: Translation  # the translation of the bot text for the current context  # noqa: E741
    k: KarenData

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    async def async_init(self):
        self.l = await self.bot.get_language(self)

        karen_guild_settings: KarenDiscordGuild | None = None
        if self.guild is not None:
            karen_guild_settings = await self.bot.karen.discord.cached.guilds.get(self.guild.id)

        karen_user = await self.bot.karen.cached.users.get(self.author.id)

        self.k = self.KarenData(user=karen_user, guild=karen_guild_settings)


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
