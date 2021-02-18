from discord.ext import commands
import traceback
import discord
import asyncio
import random


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.db = bot.get_cog("Database")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.db.populate_caches()
        self.bot.logger.info(f"\u001b[36;1mCONNECTED\u001b[0m [{self.bot.shard_count} Shards] [{len(self.bot.cogs)} Cogs]")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(1)

        for channel in guild.text_channels:
            if "general" in channel.name:
                embed = discord.Embed(
                    color=self.d.cc,
                    description="Hey y'all! Type `/help` to get started with Villager Bot!\n"
                    f"If you need any more help, check out the **[Support Server]({self.d.support})**!",
                )

                embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
                embed.set_footer(text="Made by Iapetus11#6821")

                await channel.send(embed=embed)
                break

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.db.drop_guild(guild.id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.db.clear_warns(user.id, guild.id)

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return

        self.d.msg_count += 1

        try:
            if m.type in (
                discord.MessageType.premium_guild_subscription,
                discord.MessageType.premium_guild_tier_1,
                discord.MessageType.premium_guild_tier_2,
                discord.MessageType.premium_guild_tier_3,
            ) and m.guild is not None and m.guild.id == self.d.support_server_id:
                await self.db.add_item(m.author.id, "Barrel", 1024, 1)
                await self.bot.send(m.author, f"Thanks for boosting the support server! You've received 1x **Barrel**!")
                return

            if m.content.startswith(f"<@!{self.bot.user.id}>"):
                prefix = "/"
                if m.guild is not None:
                    prefix = self.d.prefix_cache.get(m.guild.id, "/")

                lang = await self.bot.get_lang(m)

                embed = discord.Embed(color=self.d.cc, description=lang.misc.pingpong.format(prefix, self.d.support))

                embed.set_author(name="Villager Bot", icon_url=self.d.splash_logo)
                embed.set_footer(text=lang.misc.petus)

                await m.channel.send(embed=embed)
                return

            if m.guild is not None:
                if "@someone" in m.content:
                    someones = [
                        u
                        for u in m.guild.members
                        if (
                            not u.bot
                            and u.status == discord.Status.online
                            and m.author.id != u.id
                            and u.permissions_in(m.channel).read_messages
                        )
                    ]

                    if len(someones) > 0:
                        invis = ("||||\u200B" * 200)[2:-3]
                        await m.channel.send(f"@someone {invis} {random.choice(someones).mention} {m.author.mention}")
                else:
                    if not m.content.startswith(self.d.prefix_cache.get(m.guild.id, "/")):
                        if "emerald" in m.content.lower():
                            if (await self.db.fetch_guild(m.guild.id))["replies"]:
                                await m.channel.send(random.choice(self.d.hmms))
                        elif "creeper" in m.content.lower():
                            if (await self.db.fetch_guild(m.guild.id))["replies"]:
                                await m.channel.send("awww{} man".format(random.randint(1, 5) * "w"))
                        elif "reee" in m.content.lower().replace(" ", ""):
                            if (await self.db.fetch_guild(m.guild.id))["replies"]:
                                await m.channel.send(random.choice(self.d.emojis.reees))
                        else:
                            return
        except discord.errors.Forbidden:
            pass

    async def debug_error(self, ctx, e, loc=None):
        if loc is None:
            loc = self.bot.get_channel(self.d.error_channel_id)

        traceback_text = "".join(traceback.format_exception(type(e), e, e.__traceback__, 4))
        final = f"{ctx.author} (lang={ctx.__dict__.get('l', {}).get('name')}): {ctx.message.content}\n\n{traceback_text}".replace("``", "\`\`\`")

        await self.bot.send(loc, f"```py\n{final[:1023 - 6]}```")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        try:
            if isinstance(e, commands.CommandOnCooldown):
                if ctx.command.name == "mine":
                    if await self.db.fetch_item(ctx.author.id, "Efficiency I Book") is not None:
                        e.retry_after -= 0.5

                    if "haste ii potion" in self.d.chuggers.get(ctx.author.id, []):
                        e.retry_after -= 1
                    elif "haste i potion" in self.d.chuggers.get(ctx.author.id, []):
                        e.retry_after -= 0.5

                seconds = round(e.retry_after, 2)

                if seconds <= 0.05:
                    await ctx.reinvoke()
                    return

                hours = int(seconds / 3600)
                minutes = int(seconds / 60) % 60
                seconds -= round((hours * 60 * 60) + (minutes * 60), 2)

                time = ""

                if hours == 1:
                    time += f"{hours} {ctx.l.misc.time.hour}, "
                elif hours > 0:
                    time += f"{hours} {ctx.l.misc.time.hours}, "

                if minutes == 1:
                    time += f"{minutes} {ctx.l.misc.time.minute}, "
                elif minutes > 0:
                    time += f"{minutes} {ctx.l.misc.time.minutes}, "

                if seconds == 1:
                    time += f"{round(seconds, 2)} {ctx.l.misc.time.second}"
                elif seconds > 0:
                    time += f"{round(seconds, 2)} {ctx.l.misc.time.seconds}"

                await self.bot.send(ctx, random.choice(ctx.l.misc.cooldown_msgs).format(time))
            elif isinstance(e, commands.NoPrivateMessage):
                await self.bot.send(ctx, ctx.l.misc.errors.private)
            elif isinstance(e, commands.MissingPermissions):
                await self.bot.send(ctx, ctx.l.misc.errors.user_perms)
            elif isinstance(e, commands.BotMissingPermissions):
                await self.bot.send(ctx, ctx.l.misc.errors.bot_perms)
            elif isinstance(e, commands.MaxConcurrencyReached):
                await self.bot.send(ctx, ctx.l.misc.errors.concurrency)
            elif isinstance(e, commands.MissingRequiredArgument):
                await self.bot.send(ctx, ctx.l.misc.errors.missing_arg)
            elif isinstance(
                e,
                (
                    commands.BadArgument,
                    commands.errors.UnexpectedQuoteError,
                    commands.errors.ExpectedClosingQuoteError,
                    commands.errors.BadUnionArgument,
                ),
            ):
                await self.bot.send(ctx, ctx.l.misc.errors.bad_arg)
            elif ctx.__dict__.get("custom_err") == "not_ready":
                await self.bot.send(ctx, ctx.l.misc.errors.not_ready)
            elif ctx.__dict__.get("custom_err") == "bot_banned":
                pass
            elif ctx.__dict__.get("custom_err") == "econ_paused":
                await self.bot.send(ctx, ctx.l.misc.errors.nrn_buddy)
            elif ctx.__dict__.get("custom_err") == "disabled":
                await self.bot.send(ctx, ctx.l.misc.errors.disabled)
            elif ctx.__dict__.get("custom_err") == "ignore":
                return
            else:
                # errors to ignore
                for e_type in (
                    commands.CommandNotFound,
                    commands.NotOwner,
                    discord.errors.Forbidden,
                ):
                    if isinstance(e, e_type) or isinstance(e.__dict__.get("original"), e_type):
                        return

                await self.bot.send(ctx, ctx.l.misc.errors.andioop.format(self.d.support))
                await self.debug_error(ctx, e)
        except discord.errors.Forbidden:
            pass
        except Exception as e:
            if not isinstance(e.__dict__.get("original"), discord.errors.Forbidden):
                await self.debug_error(ctx, e)


def setup(bot):
    bot.add_cog(Events(bot))
