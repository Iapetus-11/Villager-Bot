import classyjson as cj
import disnake
from disnake.ext.commands import Context


class CustomContext(Context):
    def __init__(self, *args, embed_color: disnake.Color = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.embed_color = embed_color  # used in send_embed(...) and reply_embed(...)
        self.l: cj.ClassyDict = None  # the translation of the bot text for the current context

    async def send_embed(self, message: str, *, ignore_exceptions: bool = False) -> None:
        embed = disnake.Embed(color=self.embed_color, description=message)

        try:
            await self.send(embed=embed)
        except disnake.errors.HTTPException:
            if not ignore_exceptions:
                raise

    async def reply_embed(self, message: str, ping: bool = False, *, ignore_exceptions: bool = False) -> None:
        embed = disnake.Embed(color=self.embed_color, description=message)

        try:
            await self.reply(embed=embed, mention_author=ping)
        except disnake.errors.HTTPException as e:
            if e.code == 50035:  # invalid form body, happens sometimes when the message to reply to can't be found?
                await self.send_embed(message, ignore_exceptions=ignore_exceptions)
            elif not ignore_exceptions:
                raise


Ctx = CustomContext
