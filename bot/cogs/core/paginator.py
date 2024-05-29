import inspect
from typing import Any, Callable, Coroutine, Optional, Union

import discord
from discord.ext import commands

from bot.utils.ctx import Ctx
from bot.villager_bot import VillagerBotCluster

PAGE_EMBED_CALLABLE = Callable[[int], Union[discord.Embed, Coroutine[Any, Any, discord.Embed]]]


class PaginatorView(discord.ui.View):
    def __init__(self, get_page, page_count, timeout):
        super().__init__(timeout=timeout)
        self._page = 0
        self._pages = page_count
        self._get_page = get_page

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.gray)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._page = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.gray)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._page -= 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._page += 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.gray)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._page = self._pages - 1
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        # disable buttons if necessary
        self.children[0].disabled = self._page == 0
        self.children[1].disabled = self._page == 0
        self.children[2].disabled = self._page == self._pages - 1
        self.children[3].disabled = self._page == self._pages - 1

        # update message with new page/embed
        embed = await self._get_page(self._page)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)


class Paginator(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

    @staticmethod
    async def _get_page(get_page: PAGE_EMBED_CALLABLE, page: int) -> discord.Embed:
        embed = get_page(page)

        if inspect.isawaitable(embed):
            embed = await embed

        if not isinstance(embed, discord.Embed):
            raise TypeError(
                f"{getattr(type(embed), '__qualname__', type(embed))} is not a {discord.Embed.__qualname__}"
            )

        return embed

    async def paginate_embed(
        self,
        ctx: Ctx,
        get_page: PAGE_EMBED_CALLABLE,
        *,
        timeout: float = 60,
        page_count: Optional[int] = None,
    ):
        # send initial message
        embed = await self._get_page(get_page, 0)

        if page_count <= 1:
            return await ctx.reply(embed=embed, mention_author=False)

        view = PaginatorView(
            get_page=lambda page: self._get_page(get_page, page),
            page_count=page_count,
            timeout=timeout,
        )
        view.children[0].disabled = True
        view.children[1].disabled = True

        message = await ctx.reply(embed=embed, mention_author=False, view=view)
        view.message = message


async def setup(bot: VillagerBotCluster):
    await bot.add_cog(Paginator(bot))
