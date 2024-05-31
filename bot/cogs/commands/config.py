import typing

import discord
from discord.ext import commands

from bot.cogs.core.database import Database
from bot.utils.ctx import Ctx
from bot.villager_bot import VillagerBotCluster


class Config(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d

    @property
    def db(self) -> Database:
        return typing.cast(Database, self.bot.get_cog("Database"))

    @commands.group(name="config", aliases=["settings", "conf", "gamerule"], case_insensitive=True)
    async def config(self, ctx: Ctx):
        if ctx.invoked_subcommand is None:
            ctx.command.reset_cooldown(ctx)

            embed = discord.Embed(color=self.bot.embed_color)
            embed.set_author(name=ctx.l.config.main.title, icon_url=self.d.splash_logo)

            embed.add_field(
                name=ctx.l.config.main.guild_conf,
                value="".join(ctx.l.config.main.guild_content).format(ctx.prefix),
                inline=False,
            )
            embed.add_field(
                name=ctx.l.config.main.user_conf,
                value="".join(ctx.l.config.main.user_content).format(ctx.prefix),
                inline=False,
            )

            await ctx.reply(embed=embed, mention_author=False)

    @config.command(name="prefix")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_prefix(self, ctx: Ctx, prefix=None):
        if prefix is None:
            prev = await self.bot.get_prefix(ctx)
            await ctx.reply_embed(ctx.l.config.prefix.this_server.format(prev))
            return

        if len(prefix) > 15:
            await ctx.reply_embed(ctx.l.config.prefix.error_1.format(15))
            return

        for char in prefix:
            if char not in self.d.acceptable_prefix_chars:
                await ctx.reply_embed(ctx.l.config.prefix.error_2.format(char))
                return

        await self.db.set_guild_attr(ctx.guild.id, "prefix", prefix)
        self.bot.prefix_cache[ctx.guild.id] = prefix
        await ctx.reply_embed(ctx.l.config.prefix.set.format(prefix))

    @config.command(name="replies")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_replies(self, ctx: Ctx, replies: str = None):
        if replies is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            state = (
                ctx.l.config.replies.enabled if guild.do_replies else ctx.l.config.replies.disabled
            )
            await ctx.reply_embed(ctx.l.config.replies.this_server.format(state))
            return

        if replies.lower() in ("yes", "true", "on"):
            await self.db.set_guild_attr(ctx.guild.id, "do_replies", True)
            self.bot.replies_cache.add(ctx.guild.id)

            await ctx.reply_embed(ctx.l.config.replies.set.format("on"))
        elif replies.lower() in ("no", "false", "off"):
            await self.db.set_guild_attr(ctx.guild.id, "do_replies", False)

            try:
                self.bot.replies_cache.remove(ctx.guild.id)
            except KeyError:
                pass

            await ctx.reply_embed(ctx.l.config.replies.set.format("off"))
        else:
            await ctx.reply_embed(ctx.l.config.invalid.format("`on`, `off`"))

    @config.command(name="difficulty", aliases=["diff"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def config_difficulty(self, ctx: Ctx, diff: str = None):
        if diff is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await ctx.reply_embed(ctx.l.config.diff.this_server.format(guild.difficulty))
            return

        if diff.lower() == "peaceful":
            await self.db.set_guild_attr(ctx.guild.id, "difficulty", "peaceful")
            await ctx.reply_embed(ctx.l.config.diff.set.format("peaceful"))
        elif diff.lower() == "easy":
            await self.db.set_guild_attr(ctx.guild.id, "difficulty", "easy")
            await ctx.reply_embed(ctx.l.config.diff.set.format("easy"))
        elif diff.lower() == "hard":
            await self.db.set_guild_attr(ctx.guild.id, "difficulty", "hard")
            await ctx.reply_embed(ctx.l.config.diff.set.format("hard"))
        else:
            await ctx.reply_embed(ctx.l.config.invalid.format("`peaceful`, `easy`, `hard`"))

    @config.command(name="language", aliases=["lang"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_language(self, ctx: Ctx, lang: str = None):
        lang_codes = {lang.replace("_", "-") for lang in list(self.bot.l)}

        if lang is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await ctx.reply_embed(
                ctx.l.config.lang.this_server.format(
                    guild.language.replace("_", "-"),
                    "`{}`".format("`, `".join(lang_codes)),
                ),
            )
            return

        lang = lang.lower()

        if lang.lower() in lang_codes:
            await self.db.set_guild_attr(ctx.guild.id, "language", lang.replace("-", "_"))
            self.bot.language_cache[ctx.guild.id] = lang.replace("-", "_")
            ctx.l = self.bot.get_language(ctx)
            await ctx.reply_embed(ctx.l.config.lang.set.format(lang))
        else:
            await ctx.reply_embed(
                ctx.l.config.invalid.format("`{}`".format("`, `".join(lang_codes))),
            )

    @config.command(name="defaultserver", aliases=["defaultmcserver", "mcserver"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_default_mcserver(self, ctx: Ctx, mc_server: str = None):
        if mc_server is None:
            guild = await self.db.fetch_guild(ctx.guild.id)
            await ctx.reply_embed(ctx.l.config.mcs.this_server.format(guild.mc_server))
            return

        if len(mc_server) > 60:
            await ctx.reply_embed(ctx.l.config.mcs.error_1.format(60))
            return

        await self.db.set_guild_attr(ctx.guild.id, "mc_server", mc_server)
        await ctx.reply_embed(ctx.l.config.mcs.set.format(mc_server))

    @config.command(name="togglecommand", aliases=["togglecmd", "toggleenabled"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_toggle_cmd_enabled(self, ctx: Ctx, cmd: str = None):
        disabled = self.bot.disabled_commands[ctx.guild.id]

        if cmd is None:
            if len(disabled) > 0:
                await ctx.reply_embed(ctx.l.config.cmd.list_cmds.format("`, `".join(disabled)))
            else:
                await ctx.reply_embed(ctx.l.config.cmd.nope)

            return

        cmd_true = self.bot.get_command(cmd.lower())

        if (
            cmd_true is None
            or cmd_true.cog is None
            or cmd_true.cog_name in ("Owner", "Config")
            or str(cmd_true) in ("help",)
        ):
            await ctx.reply_embed(ctx.l.config.cmd.cant)
            return

        cmd_true = str(cmd_true)

        if cmd_true is None:
            await ctx.reply_embed(ctx.l.config.cmd.not_found)
            return

        if cmd_true in disabled:
            self.bot.disabled_commands[ctx.guild.id].remove(cmd_true)
            await self.db.set_cmd_usable(ctx.guild.id, cmd_true, True)
            await ctx.reply_embed(ctx.l.config.cmd.reenable.format(cmd_true))
        else:
            self.bot.disabled_commands[ctx.guild.id].add(cmd_true)
            await self.db.set_cmd_usable(ctx.guild.id, cmd_true, False)
            await ctx.reply_embed(ctx.l.config.cmd.disable.format(cmd_true))

    @config.command(name="giftalert", aliases=["gift", "give", "givealert"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_gift_alert(self, ctx: Ctx, alert=None):
        if alert is None:
            db_user = await self.db.fetch_user(ctx.author.id)
            await ctx.reply_embed(
                ctx.l.config.gift.this_user.format(
                    "enabled" if db_user.give_alert else "disabled",
                ),
            )
            return

        if alert.lower() in ("yes", "true", "on"):
            await self.db.update_user(ctx.author.id, give_alert=True)
            await ctx.reply_embed(ctx.l.config.gift.set.format("on"))
        elif alert.lower() in ("no", "false", "off"):
            await self.db.update_user(ctx.author.id, give_alert=False)
            await ctx.reply_embed(ctx.l.config.gift.set.format("off"))
        else:
            await ctx.reply_embed(ctx.l.config.invalid.format("`on`, `off`"))

    @config.command(
        name="clearrconpasswords",
        aliases=["clearpasswords", "deletepasswords", "delrconpasswords"],
    )
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def config_clear_rcon_passwords(self, ctx: Ctx):
        deleted = len(await self.db.mass_delete_user_rcon(ctx.author.id))

        if deleted < 1:
            await ctx.reply_embed(ctx.l.config.rcon.none)
        elif deleted == 1:
            await ctx.reply_embed(ctx.l.config.rcon.one)
        else:
            await ctx.reply_embed(ctx.l.config.rcon.multi.format(deleted))


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Config(bot))
