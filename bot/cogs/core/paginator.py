import asyncio
import inspect
from typing import Any, Callable, Coroutine, Optional, Union

import discord
from discord.ext import commands
from util.ctx import Ctx

from bot import VillagerBotCluster

PAGE_EMBED_CALLABLE = Callable[[int], Union[discord.Embed, Coroutine[Any, Any, discord.Embed]]]
LEFT_ARROW = "⬅️"
RIGHT_ARROW = "➡️"
NAV_EMOJIS = [LEFT_ARROW, RIGHT_ARROW]


class Paginator(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

    def _create_reaction_check(self, ctx: Ctx, msg: discord.Message) -> Callable[[discord.Reaction, discord.User], bool]:
        def predicate(r: discord.Reaction, u: discord.User):
            return (str(r.emoji) in NAV_EMOJIS) and ctx.author == u and r.message == msg

        return predicate

    async def _get_page(self, get_page: PAGE_EMBED_CALLABLE, page: int) -> discord.Embed:
        embed = get_page(page)

        if inspect.isawaitable(embed):
            embed = await embed

        if not isinstance(embed, discord.Embed):
            raise TypeError(f"{getattr(type(embed), '__qualname__', type(embed))} is not a {discord.Embed.__qualname__}")

        return embed

    async def paginate_embed(
        self, ctx: Ctx, get_page: PAGE_EMBED_CALLABLE, *, timeout: float = 60, page_count: Optional[int] = None
    ):
        page = 0
        prev_page = 0

        # send initial message and add reactions
        msg = await ctx.reply(embed=(await self._get_page(get_page, page)), mention_author=False)
        for emoji in NAV_EMOJIS:
            await msg.add_reaction(emoji)

        while True:
            prev_page = page

            # wait for a reaction from the user
            try:
                reaction, _ = await self.bot.wait_for(
                    "reaction_add", check=self._create_reaction_check(ctx, msg), timeout=timeout
                )
            except asyncio.TimeoutError:
                await asyncio.wait([msg.remove_reaction(e, ctx.me) for e in NAV_EMOJIS])
                return

            reaction: discord.Reaction
            emoji = str(reaction.emoji)

            if emoji == LEFT_ARROW:
                if page > 0:
                    page -= 1
            elif emoji == RIGHT_ARROW:
                if page < page_count - 1:
                    page += 1
            else:
                raise ValueError(emoji)  # shouldn't happen

            # update message with new page/embed
            if prev_page != page:
                msg = await msg.edit(embed=(await self._get_page(get_page, page)))

            # remove user's reaction
            await msg.remove_reaction(emoji, ctx.author)


def setup(bot: VillagerBotCluster):
    bot.add_cog(Paginator(bot))
