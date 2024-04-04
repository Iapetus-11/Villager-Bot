import asyncio
import base64
import json
import random
from contextlib import suppress
from urllib.parse import quote as urlquote

import aiohttp
import aiomcrcon as rcon
import arrow
import classyjson as cj
import discord
import minecraftstatus
from cryptography.fernet import Fernet
from discord.ext import commands

from bot.cogs.core.database import Database
from bot.utils.ctx import Ctx
from bot.utils.misc import SuppressCtxManager, fix_giphy_url
from bot.villager_bot import VillagerBotCluster

try:
    from bot.utils import tiler
except Exception:
    tiler = None


VALID_TILER_FILE_TYPES = {"jpg", "png", "jpeg", "gif", "mp4"}
TILER_MAX_DIM = 1600
TILER_MAX_DIM_GIF = 800


class Minecraft(commands.Cog):
    def __init__(self, bot: VillagerBotCluster):
        self.bot = bot

        self.d = bot.d
        self.k = bot.k

        self.aiohttp = bot.aiohttp
        self.fernet_key = Fernet(self.k.rcon_fernet_key)

        if tiler:
            self.tiler = tiler.Tiler("bot/data/block_palette.json")
        else:
            self.tiler = None

    @property
    def db(self) -> Database:
        return self.bot.get_cog("Database")

    @commands.command(name="blockify", aliases=["mcpixelart", "mcart", "mcimage", "mcvideo"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def blockify_media(self, ctx: Ctx, media_link: str = None):
        if not self.tiler:
            await ctx.send("This command is disabled because Cython isn't enabled.")
            return

        files = ctx.message.attachments

        if len(files) < 1 and not media_link:
            await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_1)
            return

        if files:
            media = files[0]
            file_name = media.filename.lower()
            is_video = file_name.endswith(".gif") or file_name.endswith(".mp4")

            if is_video and ctx.author.id not in self.bot.owner_ids:
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_2)
                return

            if getattr(media, "height", None) is None:
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_3)
                return

            try:
                media_bytes = await media.read(use_cached=True)
            except discord.HTTPException:
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_3)
                return
        else:
            if media_link.startswith("https://giphy.com/"):
                media_link = fix_giphy_url(media_link)

            link_split_dot = media_link.split(".")
            link_split_slash = media_link.split("/")

            if not (link_split_dot and link_split_slash):
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_1)
                return

            file_name = link_split_slash[-1]

            is_video = file_name.endswith(".gif") or file_name.endswith(".mp4")

            if is_video and ctx.author.id not in self.bot.owner_ids:
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_2)
                return

            if file_name.split(".")[-1] not in VALID_TILER_FILE_TYPES:
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_2)
                return

            try:
                media_bytes = await (await self.aiohttp.get(media_link)).read()
            except aiohttp.client_exceptions.InvalidURL:
                await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_1)
                return

        if file_name.split(".")[-1] not in VALID_TILER_FILE_TYPES:
            await ctx.reply_embed(ctx.l.minecraft.mcimage.stupid_2)
            return

        detailed = False

        for detailed_keyword in ("large", "high", "big", "quality", "detailed"):
            if detailed_keyword in ctx.message.content:
                detailed = True
                break

        if is_video:
            max_dim = TILER_MAX_DIM_GIF
            converter = self.tiler.convert_video
        else:
            max_dim = TILER_MAX_DIM
            converter = self.tiler.convert_image

        async with SuppressCtxManager(ctx.typing()):
            converted = await asyncio.to_thread(converter, media_bytes, max_dim, detailed)

            if is_video:
                file_name += ".gif"

            await ctx.reply(file=discord.File(converted, filename=file_name), mention_author=False)

    @commands.command(name="mcstatus", aliases=["mcping", "mcserver"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def mcstatus(self, ctx: Ctx, host=None, port: int = None):
        """Checks the status of a given Minecraft server"""

        if host is None:
            if ctx.guild is None:
                raise commands.MissingRequiredArgument(cj.ClassyDict({"name": "host"}))

            combined = (await self.db.fetch_guild(ctx.guild.id)).mc_server
            if combined is None:
                await ctx.reply_embed(ctx.l.minecraft.mcping.shortcut_error.format(ctx.prefix))
                return
        else:
            port_str = ""

            if port is not None and port != 0:
                port_str = f":{port}"

            combined = f"{host}{port_str}"

        async with SuppressCtxManager(ctx.typing()), minecraftstatus.MCStatus() as client:
            try:
                server = await client.get_server(combined.replace("/", "%2F"))
                server_card = await client.get_server_card(combined.replace("/", "%2F"))

            except minecraftstatus.errors.ServerNotFound:
                await ctx.reply(
                    embed=discord.Embed(
                        color=self.bot.embed_color,
                        title=ctx.l.minecraft.mcping.title_offline.format(
                            self.d.emojis.offline, combined
                        ),
                    ),
                    mention_author=False,
                )

                return

        player_list = server.online_players
        if player_list is None:
            player_list = ()
        else:
            player_list = [p["username"] for p in player_list]

        players_online = server.online_player_count

        embed = discord.Embed(
            color=self.bot.embed_color,
            title=ctx.l.minecraft.mcping.title_online.format(self.d.emojis.online, combined),
        )

        embed.add_field(name=ctx.l.minecraft.mcping.latency, value=f"{server.latency}ms")
        ver = server.version_info.get("brand", "Unknown")
        embed.add_field(
            name=ctx.l.minecraft.mcping.version, value=("Unknown" if ver is None else ver)
        )

        player_list_cut = []

        for p in player_list:
            if not ("§" in p or len(p) > 16 or len(p) < 3 or " " in p or "-" in p):
                player_list_cut.append(p)

        player_list_cut = player_list_cut[:24]

        if len(player_list_cut) < 1:
            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(
                    players_online, server.max_players
                ),
                value=ctx.l.minecraft.mcping.field_online_players.value,
                inline=False,
            )
        else:
            extra = ""
            if len(player_list_cut) < players_online:
                extra = ctx.l.minecraft.mcping.and_other_players.format(
                    players_online - len(player_list_cut)
                )

            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(
                    players_online, server.max_players
                ),
                value="`" + "`, `".join(player_list_cut) + "`" + extra,
                inline=False,
            )

        card = discord.File(server_card, "server_card.png")
        embed.set_image(url="attachment://server_card.png")
        if server.favicon is not None:
            embed.set_thumbnail(
                url=f"https://api.iapetus11.me/mc/server/status/{combined}/image/favicon"
            )

        await ctx.reply(embed=embed, file=card, mention_author=False)

    @commands.command(name="randommc", aliases=["randommcserver", "randomserver"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def random_mc_server(self, ctx: Ctx):
        """Checks the status of a random Minecraft server"""

        server_id = (
            await (
                await self.aiohttp.get("https://api.minecraft.global/MinecraftServers/random/")
            ).json()
        )["id"]
        server = cj.ClassyDict(
            await (
                await self.aiohttp.get(f"https://api.minecraft.global/MinecraftServers/{server_id}")
            ).json()
        )

        if server.port:
            address = server.host + ":" + str(server.port)
        else:
            address = server.host

        async with SuppressCtxManager(ctx.typing()):
            async with self.aiohttp.get(
                f"https://api.iapetus11.me/mc/server/status/{address}"  # , headers={"Authorization": self.k.villager_api}
            ) as res:  # fetch status from api
                jj = await res.json()

        if not jj["online"]:
            await self.random_mc_server(ctx)
            return

        player_list = jj.get("players", ())
        if player_list is None:
            player_list = ()
        else:
            player_list = [p["username"] for p in player_list]

        players_online = jj["online_players"]

        embed = discord.Embed(
            color=self.bot.embed_color,
            title=ctx.l.minecraft.mcping.title_plain.format(self.d.emojis.online, address),
        )

        embed.description = ctx.l.minecraft.mcping.learn_more.format(
            f"https://minecraft.global/servers/{server_id}?utm_source=villager+bot&utm_medium=discord&utm_id=1"
        )

        embed.set_footer(
            text=ctx.l.minecraft.mcping.powered_by, icon_url="https://i.ibb.co/SdZHQ4b/full-1.png"
        )

        embed.add_field(name=ctx.l.minecraft.mcping.latency, value=f'{jj["latency"]}ms')
        ver = jj["version"].get("brand", "Unknown")
        embed.add_field(
            name=ctx.l.minecraft.mcping.version, value=("Unknown" if ver is None else ver)
        )

        player_list_cut = []

        for p in player_list:
            if not ("§" in p or len(p) > 16 or len(p) < 3 or " " in p or "-" in p):
                player_list_cut.append(p)

        player_list_cut = player_list_cut[:24]

        if len(player_list_cut) < 1:
            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(
                    players_online, jj["max_players"]
                ),
                value=ctx.l.minecraft.mcping.field_online_players.value,
                inline=False,
            )
        else:
            extra = ""
            if len(player_list_cut) < players_online:
                extra = ctx.l.minecraft.mcping.and_other_players.format(
                    players_online - len(player_list_cut)
                )

            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(
                    players_online, jj["max_players"]
                ),
                value="`" + "`, `".join(player_list_cut) + "`" + extra,
                inline=False,
            )

        embed.set_image(
            url=f"https://api.iapetus11.me/mc/server/status/{address}/image?v={random.random()*100000}"
        )

        if jj["favicon"] is not None:
            embed.set_thumbnail(
                url=f"https://api.iapetus11.me/mc/server/status/{address}/image/favicon"
            )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="stealskin", aliases=["getskin", "skin", "mcskin"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def steal_skin(self, ctx: Ctx, player):
        if (
            17 > len(player) > 1
            and player.lower().strip("abcdefghijklmnopqrstuvwxyz1234567890_") == ""
        ):
            async with SuppressCtxManager(ctx.typing()):
                res = await self.aiohttp.get(
                    f"https://api.mojang.com/users/profiles/minecraft/{player}"
                )

            if res.status == 204:
                await ctx.reply_embed(ctx.l.minecraft.invalid_player)
                return

            if res.status != 200:
                await ctx.reply_embed(ctx.l.minecraft.stealskin.error)
                return

            jj = await res.json()
            uuid = jj["id"]
        elif (
            len(player) in (32, 36)
            and player.lower().strip("abcdefghijklmnopqrstuvwxyz1234567890-") == ""
        ):  # player is a uuid
            uuid = player.replace("-", "")
        else:
            await ctx.reply_embed(ctx.l.minecraft.invalid_player)
            return

        async with SuppressCtxManager(ctx.typing()):
            res = await self.aiohttp.get(
                f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
            )

        if res.status != 200:
            await ctx.reply_embed(ctx.l.minecraft.stealskin.error)
            return

        profile = await res.json()
        skin_url = None

        for prop in profile["properties"]:
            if prop["name"] == "textures":
                skin_url = (
                    json.loads(base64.b64decode(prop["value"]))["textures"]
                    .get("SKIN", {})
                    .get("url")
                )
                break

        if skin_url is None:
            await ctx.reply_embed(ctx.l.minecraft.stealskin.no_skin)
            return

        embed = discord.Embed(
            color=self.bot.embed_color,
            description=ctx.l.minecraft.stealskin.embed_desc.format(profile["name"], skin_url),
        )

        embed.set_thumbnail(url=skin_url)
        embed.set_image(url=f"https://visage.surgeplay.com/full/{uuid}.png")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(
        name="mcprofile", aliases=["minecraftprofile", "nametouuid", "uuidtoname", "mcp"]
    )
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def minecraft_profile(self, ctx: Ctx, player):
        if (
            17 > len(player) > 1
            and player.lower().strip("abcdefghijklmnopqrstuvwxyz1234567890_") == ""
        ):
            async with SuppressCtxManager(ctx.typing()):
                res = await self.aiohttp.get(
                    f"https://api.mojang.com/users/profiles/minecraft/{player}"
                )

            if res.status == 204:
                await ctx.reply_embed(ctx.l.minecraft.invalid_player)
                return

            if res.status != 200:
                await ctx.reply_embed(ctx.l.minecraft.profile.error)
                return

            jj = await res.json()
            uuid = jj["id"]
        elif (
            len(player) in (32, 36)
            and player.lower().strip("abcdefghijklmnopqrstuvwxyz1234567890-") == ""
        ):  # player is a uuid
            uuid = player.replace("-", "")
        else:
            await ctx.reply_embed(ctx.l.minecraft.invalid_player)
            return

        async with SuppressCtxManager(ctx.typing()):
            res = await self.aiohttp.get(
                f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
            )

        if res.status == 204:
            await ctx.reply_embed(ctx.l.minecraft.invalid_player)
            return

        if res.status != 200:
            await ctx.reply_embed(ctx.l.minecraft.profile.error)
            return

        profile = cj.classify(await res.json())

        skin_url = None
        cape_url = None

        for prop in profile["properties"]:
            if prop["name"] == "textures":
                textures = json.loads(base64.b64decode(prop["value"]))["textures"]
                skin_url = textures.get("SKIN", {}).get("url")
                cape_url = textures.get("CAPE", {}).get("url")

                break

        # name_hist = "\uFEFF"

        # for i, name in enumerate(list(reversed(names))[:20]):
        #     time = name.get("changedToAt")
        #
        #     if time is None:
        #         time = ctx.l.minecraft.profile.first
        #     else:
        #         time = arrow.Arrow.fromtimestamp(time)
        #         time = (
        #             time.format("MMM D, YYYY", locale=ctx.l.lang)
        #             + ", "
        #             + time.humanize(locale=ctx.l.lang)
        #         )
        #
        #     name_hist += f"**{len(names)-i}.** `{name.name}` - {time}\n"

        embed = discord.Embed(
            color=self.bot.embed_color, title=ctx.l.minecraft.profile.mcpp.format(profile.name)
        )

        if skin_url is not None:
            embed.description = f"**[{ctx.l.minecraft.profile.skin}]({skin_url})**"

        if cape_url is not None:
            embed.description += f" | **[{ctx.l.minecraft.profile.cape}]({cape_url})**"
        # else:
        #     embed.description += f" | {ctx.l.minecraft.profile.nocape}"

        embed.set_thumbnail(url=f"https://crafatar.com/avatars/{uuid}.png")

        embed.add_field(
            name=":link: UUID",
            value=f"`{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}`\n`{uuid}`",
            inline=False,
        )
        # embed.add_field(
        #     name=(":label: " + ctx.l.minecraft.profile.hist), value=name_hist, inline=False
        # )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="nametoxuid", aliases=["grabxuid", "benametoxuid", "bename"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def name_to_xuid(self, ctx: Ctx, *, username):
        """Turns a Minecraft BE username/gamertag into an xuid"""

        async with SuppressCtxManager(ctx.typing()):
            res = await self.aiohttp.get(
                f"https://xapi.us/v2/xuid/{urlquote(username)}", headers={"X-AUTH": self.k.xapi_key}
            )

        if res.status != 200:
            await ctx.reply_embed(ctx.l.minecraft.invalid_player)
            return

        xuid = f'{"0"*8}-{"0000-"*3}{hex(int(await res.text())).strip("0x")}'

        await ctx.reply_embed(f'**{username}**: `{xuid}` / `{xuid[20:].replace("-", "").upper()}`')

    @commands.command(name="mccolors", aliases=["minecraftcolors", "chatcolors", "colorcodes"])
    async def color_codes(self, ctx: Ctx):
        """Shows the Minecraft chat color codes"""

        embed = discord.Embed(
            color=self.bot.embed_color, description=ctx.l.minecraft.mccolors.embed_desc
        )

        embed.set_author(name=ctx.l.minecraft.mccolors.embed_author_name)

        cs = ctx.l.minecraft.mccolors.formatting_codes

        embed.add_field(
            name=ctx.l.minecraft.mccolors.colors,
            value=f"<:red:697541699706028083> **{cs.red}** `§c`\n"
            f"<:yellow:697541699743776808> **{cs.yellow}** `§e`\n"
            f"<:green:697541699316219967> **{cs.green}** `§a`\n"
            f"<:aqua:697541699173613750> **{cs.aqua}** `§b`\n"
            f"<:blue:697541699655696787> **{cs.blue}** `§9`\n"
            f"<:light_purple:697541699546775612> **{cs.light_purple}** `§d`\n"
            f"<:white:697541699785719838> **{cs.white}** `§f`\n"
            f"<:gray:697541699534061630> **{cs.gray}** `§7`\n",
        )

        embed.add_field(
            name=ctx.l.minecraft.mccolors.more_colors,
            value=f"<:dark_red:697541699488055426> **{cs.dark_red}** `§4`\n"
            f"<:gold:697541699639050382> **{cs.gold}** `§6`\n"
            f"<:dark_green:697541699500769420> **{cs.dark_green}** `§2`\n"
            f"<:dark_aqua:697541699475472436> **{cs.dark_aqua}** `§3`\n"
            f"<:dark_blue:697541699488055437> **{cs.dark_blue}** `§1`\n"
            f"<:dark_purple:697541699437592666> **{cs.dark_purple}** `§5`\n"
            f"<:dark_gray:697541699471278120> **{cs.dark_gray}** `§8`\n"
            f"<:black:697541699496444025> **{cs.black}** `§0`\n",
        )

        embed.add_field(
            name=ctx.l.minecraft.mccolors.formatting,
            value=f"<:bold:697541699488186419> **{cs.bold}** `§l`\n"
            f"<:strikethrough:697541699768942711> ~~{cs.strikethrough}~~ `§m`\n"
            f"<:underline:697541699806953583> {cs.underline} `§n`\n"
            f"<:italic:697541699152379995> *{cs.italic}* `§o`\n"
            f"<:obfuscated:697541699769204736> ||{cs.obfuscated}|| `§k`\n"
            f"<:reset:697541699697639446> {cs.reset} `§r`\n",
        )

        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="buildidea", aliases=["idea"])
    async def build_idea(self, ctx: Ctx):
        """Sends a random "build idea" which you could create"""

        prefix = random.choice(self.d.build_ideas["prefixes"])
        idea = random.choice(self.d.build_ideas["ideas"])

        await ctx.reply_embed(f"{prefix} {idea}!")

    @commands.command(name="rcon", aliases=["mccmd"])
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.guild_only()
    async def rcon_command(self, ctx: Ctx, *, cmd):
        db_guild = await self.db.fetch_guild(ctx.guild.id)

        if db_guild.mc_server is None:
            await ctx.reply_embed(ctx.l.minecraft.rcon.stupid_1.format(ctx.prefix))
            return

        db_user_rcon = await self.db.fetch_user_rcon(ctx.author.id, db_guild.mc_server)

        if db_user_rcon is None:
            try:
                await self.bot.send_embed(ctx.author, ctx.l.minecraft.rcon.port)
            except Exception:
                await ctx.reply_embed(ctx.l.minecraft.rcon.dm_error, True)
                return

            try:
                port_msg = await self.bot.wait_for(
                    "fwd_dm",
                    check=(lambda dm: dm.user_id == ctx.author.id),
                    timeout=60,
                )
            except asyncio.TimeoutError:
                try:
                    await self.bot.send_embed(ctx.author, ctx.l.minecraft.rcon.msg_timeout)
                except (discord.Forbidden, discord.HTTPException):
                    pass

                return

            try:
                rcon_port = int(port_msg["content"])

                if 0 > rcon_port > 65535:
                    rcon_port = 25575
            except (ValueError, TypeError):
                rcon_port = 25575

            try:
                await self.bot.send_embed(ctx.author, ctx.l.minecraft.rcon.passw)
            except Exception:
                await ctx.reply_embed(ctx.l.minecraft.rcon.dm_error, True)
                return

            try:
                auth_msg = await self.bot.wait_for(
                    "fwd_dm",
                    check=(lambda dm: dm.user_id == ctx.author.id),
                    timeout=60,
                )
            except asyncio.TimeoutError:
                try:
                    await self.bot.send_embed(ctx.author, ctx.l.minecraft.rcon.msg_timeout)
                except (discord.Forbidden, discord.HTTPException):
                    pass

                return

            password = auth_msg["content"]
        else:
            rcon_port = db_user_rcon["rcon_port"]
            password = self.fernet_key.decrypt(db_user_rcon["password"].encode("utf-8")).decode(
                "utf-8"
            )  # decrypt to plaintext

        with suppress(Exception):
            await ctx.defer()

        try:
            rcon_con = self.bot.rcon_cache.get((ctx.author.id, db_guild.mc_server))

            if rcon_con is None:
                rcon_con = rcon.Client(db_guild.mc_server.split(":")[0], rcon_port, password)
                self.bot.rcon_cache[(ctx.author.id, db_guild.mc_server)] = (
                    rcon_con,
                    arrow.utcnow(),
                )
            else:
                rcon_con = rcon_con[0]
                self.bot.rcon_cache[(ctx.author.id, db_guild.mc_server)] = (
                    rcon_con,
                    arrow.utcnow(),
                )

            await rcon_con.connect(timeout=2.5)
        except Exception as e:
            if isinstance(e, rcon.IncorrectPasswordError):
                await ctx.reply_embed(ctx.l.minecraft.rcon.stupid_2)
            else:
                await ctx.reply_embed(ctx.l.minecraft.rcon.err_con)

            await self.db.delete_user_rcon(ctx.author.id, db_guild.mc_server)
            await rcon_con.close()
            self.bot.rcon_cache.pop((ctx.author.id, db_guild.mc_server), None)

            return

        if db_user_rcon is None:
            encrypted_password = self.fernet_key.encrypt(password.encode("utf-8")).decode("utf-8")
            await self.db.add_user_rcon(
                ctx.author.id, db_guild.mc_server, rcon_port, encrypted_password
            )

        try:
            resp = await rcon_con.send_cmd(cmd[:1445])
        except Exception:
            await ctx.reply_embed(ctx.l.minecraft.rcon.err_cmd)
            await rcon_con.close()
            self.bot.rcon_cache.pop((ctx.author.id, db_guild.mc_server), None)

            return

        # strip color codes
        resp_text = ""
        for i in range(0, len(resp[0])):
            if resp[0][i] != "§" and (i == 0 or resp[0][i - 1] != "§"):
                resp_text += resp[0][i]

        await ctx.reply(
            "```\uFEFF{}```".format(resp_text.replace("\\n", "\n")[: 2000 - 7]),
            mention_author=False,
        )


async def setup(bot: VillagerBotCluster) -> None:
    await bot.add_cog(Minecraft(bot))
