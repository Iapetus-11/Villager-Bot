from discord.ext.commands import Context
import discord


class BetterContext(Context):
    def __init__(self, *args, embed_color: discord.Color = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.embed_color = embed_color  # used in send_embed(...) and reply_embed(...)
        self.l = None  # the translation of the bot text for the current context

    async def send_embed(self, message: str, *, ignore_exceptions: bool = False) -> None:
        try:
            await self.send(embed=discord.Embed(color=self.embed_color, description=message))
        except (discord.errors.Forbidden, discord.errors.HTTPException):
            if not ignore_exceptions:
                raise

    async def reply_embed(self, message: str, ping: bool = False, *, ignore_exceptions: bool = False) -> None:
        try:
            await self.reply(embed=discord.Embed(color=self.embed_color, description=message), mention_author=ping)
        except discord.errors.HTTPException as e:
            if e.code == 50035:  # invalid form body, happens sometimes when the message to reply to can't be found?
                await self.send_embed(message, ignore_exceptions=ignore_exceptions)
            elif not ignore_exceptions:
                raise
        except discord.errors.Forbidden:
            if not ignore_exceptions:
                raise
