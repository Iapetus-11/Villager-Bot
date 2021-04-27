from discord.ext import commands
import traceback
import discord
import asyncio
import random

from util.handlers import handle_message, handle_error
from util.misc import cooldown_logic


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d
        self.v = bot.v

        self.db = bot.get_cog("Database")

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"\u001b[36;1mCONNECTED\u001b[0m [{self.bot.shard_count} Shards] [{len(self.bot.cogs)} Cogs]")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(1)

        for channel in guild.text_channels:
            if "general" in channel.name:
                embed = discord.Embed(
                    color=self.d.cc,
                    description=f"Hey y'all! Type `{self.d.default_prefix}help` to get started with Villager Bot!\n"
                    f"If you need any more help, check out the **[Support Server]({self.d.support})**!",
                )

                embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
                embed.set_footer(text=f"Made by Iapetus11  |  {self.d.default_prefix}rules for the rules!")

                await channel.send(embed=embed)
                break

            await asyncio.sleep(0)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.db.drop_guild(guild.id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.db.clear_warns(user.id, guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == self.d.support_server_id:
            await self.bot.wait_until_ready()
            await self.bot.update_support_member_role(member)

    @commands.Cog.listener()
    async def on_message(self, m):
        try:
            await asyncio.gather(*handle_message(self, m))
        except discord.errors.Forbidden:
            pass

    async def debug_error(self, ctx, e, loc=None):
        self.bot.statcord.error_count += 1

        if loc is None:
            loc = self.bot.get_channel(self.d.error_channel_id)

        try:
            ctx.message.content
        except AttributeError:
            ctx.message.content = None

        traceback_text = "".join(traceback.format_exception(type(e), e, e.__traceback__, 4))
        final = f"{ctx.author} (lang={getattr(ctx, 'l', {}).get('lang')}): {ctx.message.content}\n\n{traceback_text}".replace(
            "``", "\`\`\`"
        )

        await self.bot.send(loc, f"```py\n{final[:1023 - 6]}```")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        try:
            if isinstance(e, commands.CommandOnCooldown):
                if ctx.command.name == "mine":
                    if await self.db.fetch_item(ctx.author.id, "Efficiency I Book") is not None:
                        e.retry_after -= 0.5

                    if "haste ii potion" in self.v.chuggers.get(ctx.author.id, []):
                        e.retry_after -= 1
                    elif "haste i potion" in self.v.chuggers.get(ctx.author.id, []):
                        e.retry_after -= 0.5

                seconds = round(e.retry_after, 2)

                if seconds <= 0.05:
                    await ctx.reinvoke()
                    return

                time = cooldown_logic(ctx, seconds)

                await self.bot.send(ctx, random.choice(ctx.l.misc.cooldown_msgs).format(time))
            else:
                await asyncio.gather(*handle_error(self, ctx, e))
        except discord.errors.Forbidden:
            pass
        except BaseException as e:
            if not isinstance(getattr(e, "original", None), discord.errors.Forbidden):
                await self.debug_error(ctx, e)


def setup(bot):
    bot.add_cog(Events(bot))
