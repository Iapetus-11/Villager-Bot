import aiohttp
import asyncio
import base64
import concurrent.futures
import discord
import json
import socket
from discord.ext import commands
from functools import partial
from mcstatus import MinecraftServer
from pyraklib.protocol.EncapsulatedPacket import EncapsulatedPacket
from pyraklib.protocol.UNCONNECTED_PING import UNCONNECTED_PING
from pyraklib.protocol.UNCONNECTED_PONG import UNCONNECTED_PONG
from random import choice
from time import sleep


class Minecraft(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.ses = aiohttp.ClientSession()

        self.g = self.bot.get_cog("Global")

        with open("data/build_ideas.json", "r") as stuff:
            _json = json.load(stuff)
            self.first = _json["first"]
            self.prenouns = _json["prenouns"]
            self.nouns = _json["nouns"]
            self.colors = _json["colors"]
            self.sizes = _json["sizes"]

    def cog_unload(self):
        self.bot.loop.create_task(self.ses.close())

    def vanilla_pe_ping(self, ip, port):
        ping = UNCONNECTED_PING()
        ping.pingID = 4201
        ping.encode()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(0)
        try:
            s.sendto(ping.buffer, (socket.gethostbyname(ip), port))
            sleep(1)
            recv_data = s.recvfrom(2048)
        except BlockingIOError:
            return False, 0
        except socket.gaierror:
            return False, 0
        pong = UNCONNECTED_PONG()
        pong.buffer = recv_data[0]
        pong.decode()
        s_info = str(pong.serverName)[2:-2].split(";")
        p_count = s_info[4]
        return True, p_count

    def standard_je_ping(self, combined_server):
        try:
            status = MinecraftServer.lookup(combined_server).status()
        except Exception:
            return False, 0, None, None

        return True, status.players.online, None, status.latency

    async def unified_mc_ping(self, server_str, _port=None, _ver=None):
        if ":" in server_str and _port is None:
            split = server_str.split(":")
            ip = split[0]
            port = int(split[1])
        else:
            ip = server_str
            port = _port

        if port is None:
            str_port = ""
        else:
            str_port = f":{port}"

        if _ver == "je":
            # ONLY JE servers
            standard_je_ping_partial = partial(self.standard_je_ping, f"{ip}{str_port}")
            with concurrent.futures.ThreadPoolExecutor() as pool:
                s_je_online, s_je_player_count, s_je_players, s_je_latency = await self.bot.loop.run_in_executor(pool,
                                                                                              standard_je_ping_partial)
            if s_je_online:
                return {"online": True, "player_count": s_je_player_count, "players": s_je_players, "ping": s_je_latency, "version": "Java Edition"}

            return {"online": False, "player_count": 0, "players": None, "ping": None, "version": None}
        elif _ver == "api":
            # JE & PocketMine
            resp = await self.ses.get(f"https://api.mcsrvstat.us/2/{ip}{str_port}")
            jj = await resp.json()
            if jj.get("online"):
                return {"online": True, "player_count": jj.get("players", {}).get("online", 0), "players": jj.get("players", {}).get("list"), "ping": None,
                        "version": jj.get("software")}
            return {"online": False, "player_count": 0, "players": None, "ping": None, "version": None}
        elif _ver == "be":
            # Vanilla MCPE / Bedrock Edition (USES RAKNET)
            vanilla_pe_ping_partial = partial(self.vanilla_pe_ping, ip, port if port is not None else 19132)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pe_online, pe_p_count = await self.bot.loop.run_in_executor(pool, vanilla_pe_ping_partial)
            if pe_online:
                return {"online": True, "player_count": pe_p_count, "players": None, "ping": None, "version": "Vanilla Bedrock Edition"}
            return {"online": False, "player_count": 0, "players": None, "ping": None, "version": None}
        else:
            tasks = [
                self.bot.loop.create_task(self.unified_mc_ping(ip, port, "je")),
                self.bot.loop.create_task(self.unified_mc_ping(ip, port, "api")),
                self.bot.loop.create_task(self.unified_mc_ping(ip, port, "be"))
            ]

            for task in tasks:
                while not task.done():
                    await asyncio.sleep(.05)

            for task in tasks:
                if task.result().get("online") is True:
                    return task.result()

            return {"online": False, "player_count": 0, "players": None, "ping": None, "version": None}

    @commands.command(name="mcping")
    async def mc_ping(self, ctx, server: str, port: int = None):
        async with ctx.typing():
            status = await self.unified_mc_ping(server, port)

        title = f"<:a:730460448339525744> {server}{(':' + str(port)) if port is not None else ''} is online."

        if status.get("online") is False:
            embed = discord.Embed(color=discord.Color.green(),
                                  title=f"<:b:730460448197050489> {server}{(':' + str(port)) if port is not None else ''} is offline.")
            await ctx.send(embed=embed)
            return

        ps_list = status.get("players")

        embed = discord.Embed(color=discord.Color.green(), title=title)

        ping = status.get("ping", "Not Available")

        if ps_list is None:
            embed.add_field(name="Players Online", value=status.get("player_count"))

        embed.add_field(name="Latency/Ping", value=ping if ping != "None" else "Not Available")
        embed.add_field(name="Version", value=status.get('version'), inline=False)

        if ps_list is not None:
            ps_list_cut = ps_list[:20]
            if len(ps_list_cut) == 0:
                ps_list_cut.append("No players online.")

            if len(ps_list_cut) < len(ps_list):
                ps_list_cut.append(f"and {len(ps_list)-len(ps_list_cut)} others...")

            embed.add_field(name=f"Players Online ({len(ps_list)} Total)",
                            value=discord.utils.escape_markdown(', '.join(ps_list_cut)),
                            inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="stealskin", aliases=["skinsteal", "skin"])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def skinner(self, ctx, *, gamertag: str):
        response = await self.ses.get(f"https://api.mojang.com/users/profiles/minecraft/{gamertag}")
        if response.status == 204:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That player doesn't exist!"))
            return
        uuid = json.loads(await response.text()).get("id")
        if uuid is None:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That player doesn't exist!"))
            return
        response = await self.ses.get(
            f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}?unsigned=false")
        content = json.loads(await response.text())
        if "error" in content:
            if content["error"] == "TooManyRequestsException":
                await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="Hey! Slow down!"))
                return
        if len(content["properties"]) == 0:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                               description="This user's skin can't be stolen for some reason..."))
            return
        undec = base64.b64decode(content["properties"][0]["value"])
        try:
            url = json.loads(undec)["textures"]["SKIN"]["url"]
        except Exception:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                               description="An error occurred while fetching that skin!"))
            return
        skin_embed = discord.Embed(color=discord.Color.green(),
                                   description=f"{gamertag}'s skin\n[**[Download]**]({url})")
        skin_embed.set_thumbnail(url=url)
        skin_embed.set_image(url=f"https://mc-heads.net/body/{gamertag}")
        await ctx.send(embed=skin_embed)

    @commands.command(name="nametouuid", aliases=["uuid", "getuuid"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def get_uuid(self, ctx, *, gamertag: str):
        r = await self.ses.post("https://api.mojang.com/profiles/minecraft", json=[gamertag])
        j = json.loads(await r.text())  # [0]['id']
        if not j:
            await ctx.send(
                embed=discord.Embed(color=discord.Color.green(), description="That user could not be found."))
            return
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{gamertag}: ``{j[0]['id']}``"))

    @commands.command(name="uuidtoname", aliases=["getgamertag"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def get_gamertag(self, ctx, uuid: str):
        if not 30 < len(uuid) < 34:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That's not a valid mc uuid!"))
            return
        response = await self.ses.get(f"https://api.mojang.com/user/profiles/{uuid}/names")
        if response.status == 204:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(), description="That player doesn't exist!"))
            return
        j = json.loads(await response.text())
        name = j[len(j) - 1]["name"]
        await ctx.send(embed=discord.Embed(color=discord.Color.green(), description=f"{uuid}: ``{name}``"))

    @commands.command(name="mcsales", aliases=["minecraftsales"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def mc_sales(self, ctx):
        r = await self.ses.post("https://api.mojang.com/orders/statistics",
                                json={"metricKeys": ["item_sold_minecraft", "prepaid_card_redeemed_minecraft"]})
        j = json.loads(await r.text())
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description=f"**{j['total']}** total Minecraft copies sold, **{round(j['saleVelocityPerSeconds'], 3)}** copies sold per second."))

    @commands.command(name="randomserver", aliases=["randommc", "randommcserver", "mcserver", "minecraftserver"])
    async def random_mc_server(self, ctx):
        s = choice(self.g.mcServers)
        try:
            online = MinecraftServer.lookup(s['ip'] + ":" + str(s['port'])).status()
            stat = "<:online:692764696075304960>"
        except Exception:
            stat = "<:offline:692764696431951872>"
        await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                           description=f"{stat} \uFEFF ``{s['ip']}:{s['port']}`` {s['version']} ({s['type']})\n{s['note']}"))

    @commands.command(name="buildidea", aliases=["idea"])
    async def build_idea(self, ctx):
        if choice([True, False]):
            await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                               description=f"{choice(self.first)} {choice(self.prenouns)}{choice(['!', ''])}"))
        else:
            await ctx.send(embed=discord.Embed(color=discord.Color.green(),
                                               description=f"{choice(self.first)} a {choice(self.sizes)}, {choice(self.colors)} {choice(self.nouns)}{choice(['!', ''])}"))

    @commands.command(name="colorcodes", aliases=["mccolorcodes", "colors", "cc"])
    async def mc_color_codes(self, ctx):
        embed = discord.Embed(color=discord.Color.green(),
                              description="Text in Minecraft can be formatted using different codes and\nthe section (``§``) sign.")
        embed.set_author(name="Minecraft Formatting Codes")
        embed.add_field(name="Color Codes", value="<:red:697541699706028083> **Red** ``§c``\n"
                                                  "<:yellow:697541699743776808> **Yellow** ``§e``\n"
                                                  "<:green:697541699316219967> **Green** ``§a``\n"
                                                  "<:aqua:697541699173613750> **Aqua** ``§b``\n"
                                                  "<:blue:697541699655696787> **Blue** ``§9``\n"
                                                  "<:light_purple:697541699546775612> **Light Purple** ``§d``\n"
                                                  "<:white:697541699785719838> **White** ``§f``\n"
                                                  "<:gray:697541699534061630> **Gray** ``§7``\n")
        embed.add_field(name="Color Codes", value="<:dark_red:697541699488055426> **Dark Red** ``§4``\n"
                                                  "<:gold:697541699639050382> **Gold** ``§6``\n"
                                                  "<:dark_green:697541699500769420> **Dark Green** ``§2``\n"
                                                  "<:dark_aqua:697541699475472436> **Dark Aqua** ``§3``\n"
                                                  "<:dark_blue:697541699488055437> **Dark Blue** ``§1``\n"
                                                  "<:dark_purple:697541699437592666> **Dark Purple** ``§5``\n"
                                                  "<:dark_gray:697541699471278120> **Dark Gray** ``§8``\n"
                                                  "<:black:697541699496444025> **Black** ``§0``\n")
        embed.add_field(name="Formatting Codes", value="<:bold:697541699488186419> **Bold** ``§l``\n"
                                                       "<:strikethrough:697541699768942711> ~~Strikethrough~~ ``§m``\n"
                                                       "<:underline:697541699806953583> __Underline__ ``§n``\n"
                                                       "<:italic:697541699152379995> *Italic* ``§o``\n"
                                                       "<:obfuscated:697541699769204736> ||Obfuscated|| ``§k``\n"
                                                       "<:reset:697541699697639446> Reset ``§r``\n")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Minecraft(bot))
