from discord.ext import commands, tasks
from bs4 import BeautifulSoup as bs
import concurrent.futures
import functools
import aiohttp
import discord
import random
import base64
import json
import os


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.mosaic = __import__('util.mosaic').mosaic  # so I can pull and use the new code from the new changes

        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

        self.ses = aiohttp.ClientSession(loop=self.bot.loop)

        self.d.mcserver_list = []
        self.update_server_list.start()

    def cog_unload(self):
        del self.mosaic
        self.update_server_list.cancel()
        self.bot.loop.create_task(self.ses.close())

    @tasks.loop(hours=2)
    async def update_server_list(self):
        self.bot.logger.info('scraping mc-lists.org...')

        servers_nice = []

        for i in range(1, 26):
            async with self.ses.get(f'https://mc-lists.org/pg.{i}') as res:
                soup = bs(await res.text(), 'html.parser')
                elems = soup.find(class_='ui striped table servers serversa').find_all('tr')

                for elem in elems:
                    split = str(elem).split('\n')
                    url = split[9][9:-2]
                    ip = split[16][46:-2].replace('https://', '').replace('http://', '')
                    servers_nice.append((ip, url,))

        self.d.mcserver_list = list(set(servers_nice)) + self.d.additional_mcservers

        self.bot.logger.info('finished scraping mc-lists.org')

    @update_server_list.before_loop
    async def before_update_server_list(self):
        await self.bot.wait_until_ready()

    @commands.command(name='mcimage', aliases=['mcpixelart', 'mcart', 'mcimg'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mcpixelart(self, ctx):
        files = ctx.message.attachments

        if len(files) < 1:
            await self.bot.send(ctx, ctx.l.minecraft.mcimage.stupid_1)
            return
        else:
            img = files[0]

        if img.filename.lower()[-4:] not in ('.jpg', '.png',) and not img.filename.lower()[-5:] in ('.jpeg'):
            await self.bot.send(ctx, ctx.l.minecraft.mcimage.stupid_2)
            return

        try:
            img.height
        except Exception:
            await self.bot.send(ctx, ctx.l.minecraft.mcimage.stupid_3)
            return

        detailed = ('large' in ctx.message.content or 'high' in ctx.message.content)

        with ctx.typing():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                mosaic_gen_partial = functools.partial(self.mosaic.generate, await img.read(use_cached=True), 1600, detailed)
                _, img_bytes = await self.bot.loop.run_in_executor(pool, mosaic_gen_partial)

            filename = f'{ctx.message.id}-{img.width}x{img.height}.png'

            with open(filename, 'wb+') as tmp:
                tmp.write(img_bytes)

            await ctx.send(file=discord.File(filename, filename=img.filename))

        os.remove(filename)

    @commands.command(name='mcping', aliases=['mcstatus'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def mcping(self, ctx, host=None, port: int = None):
        """Checks the status of a given Minecraft server"""

        if host is None:
            combined = (await self.db.fetch_guild(ctx.guild.id))['mcserver']
            if combined is None:
                await self.bot.send(ctx, ctx.l.minecraft.mcping.shortcut_error.format(ctx.prefix))
                return
        else:
            port_str = ''
            if port is not None and port != 0:
                port_str = f':{port}'
            combined = f'{host}{port_str}'

        with ctx.typing():
            async with self.ses.get(f'https://betterapi.net/mc/mcstatus/{combined}', headers={'Authorization': self.d.vb_api_key}) as res:  # fetch status from api
                jj = await res.json()

        if not jj['success'] or not jj['online']:
            embed = discord.Embed(color=self.d.cc, title=ctx.l.minecraft.mcping.title_offline.format(self.d.emojis.offline, combined))
            await ctx.send(embed=embed)
            return

        player_list = jj.get('players_names', [])
        if player_list is None: player_list = []

        players_online = jj['players_online']  # int@

        embed = discord.Embed(color=self.d.cc, title=ctx.l.minecraft.mcping.title_online.format(self.d.emojis.online, combined))

        embed.add_field(name=ctx.l.minecraft.mcping.latency, value=jj['latency'])
        ver = jj['version'].get('brand', 'Unknown')
        embed.add_field(name=ctx.l.minecraft.mcping.version, value=('Unknown' if ver is None else ver))

        player_list_cut = player_list[:24]

        if len(player_list_cut) < 1:
            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(players_online, jj['players_max']),
                value=ctx.l.minecraft.mcping.field_online_players.value,
                inline=False
            )
        else:
            extra = ''
            if len(player_list_cut) < players_online:
                extra = ctx.l.minecraft.mcping.and_other_players.format(players_online - len(player_list_cut))

            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(players_online, jj['players_max']),
                value='`' + '`, `'.join(player_list_cut) + '`' + extra,
                inline=False
            )

        embed.set_image(url=f'https://betterapi.net/mc/servercard/{combined}?v={random.random()*100000}')

        if jj['favicon'] is not None:
            embed.set_thumbnail(url=f'https://betterapi.net/mc/serverfavicon/{combined}')

        await ctx.send(embed=embed)

    @commands.command(name='randommc', aliases=['randommcserver', 'randomserver'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def random_mc_server(self, ctx):
        """Checks the status of a random Minecraft server"""

        s = random.choice(self.d.mcserver_list)
        combined = s[0]

        with ctx.typing():
            async with self.ses.get(f'https://betterapi.net/mc/mcstatus/{combined}', headers={'Authorization': self.d.vb_api_key}) as res:  # fetch status from api
                jj = await res.json()

        if not jj['success'] or not jj['online']:
            self.d.mcserver_list.pop(self.d.mcserver_list.index(s))
            await self.random_mc_server(ctx)
            return

        player_list = jj.get('players_names', [])
        if player_list is None: player_list = []

        players_online = jj['players_online']  # int@

        embed = discord.Embed(color=self.d.cc, title=ctx.l.minecraft.mcping.title_online.format(self.d.emojis.online, combined))

        if s[1] is not None:
            embed.description = ctx.l.minecraft.mcping.learn_more.format(s[1])

        embed.add_field(name=ctx.l.minecraft.mcping.latency, value=jj['latency'])
        ver = jj['version'].get('brand', 'Unknown')
        embed.add_field(name=ctx.l.minecraft.mcping.version, value=('Unknown' if ver is None else ver))

        player_list_cut = player_list[:24]

        if len(player_list_cut) < 1:
            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(players_online, jj['players_max']),
                value=ctx.l.minecraft.mcping.field_online_players.value,
                inline=False
            )
        else:
            extra = ''
            if len(player_list_cut) < players_online:
                extra = ctx.l.minecraft.mcping.and_other_players.format(players_online - len(player_list_cut))

            embed.add_field(
                name=ctx.l.minecraft.mcping.field_online_players.name.format(players_online, jj['players_max']),
                value='`' + '`, `'.join(player_list_cut) + '`' + extra,
                inline=False
            )

        embed.set_image(url=f'https://betterapi.net/mc/servercard/{combined}?v={random.random()*100000}')

        if jj['favicon'] is not None:
            embed.set_thumbnail(url=f'https://betterapi.net/mc/serverfavicon/{combined}')

        await ctx.send(embed=embed)

    @commands.command(name='stealskin', aliases=['getskin', 'skin', 'mcskin'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def steal_skin(self, ctx, player):
        """"steals" the skin of a Minecraft player"""

        with ctx.typing():
            res = await self.ses.get(f'https://api.mojang.com/users/profiles/minecraft/{player}')

        if res.status == 204:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        uuid = (await res.json()).get('id')

        if uuid is None:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        res_profile = await self.ses.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}?unsigned=false')
        profile_content = await res_profile.json()

        if 'error' in profile_content or len(profile_content['properties']) == 0:
            await self.bot.send(ctx, ctx.l.minecraft.stealskin.error_1)
            return

        try:
            decoded_jj = json.loads(base64.b64decode(profile_content['properties'][0]['value']))
            skin_url = decoded_jj['textures']['SKIN']['url']
        except Exception:
            await self.bot.send(ctx, ctx.l.minecraft.stealskin.error_1)
            return

        embed = discord.Embed(color=self.d.cc, description=ctx.l.minecraft.stealskin.embed_desc.format(player, skin_url))
        embed.set_thumbnail(url=skin_url)
        embed.set_image(url=f'https://mc-heads.net/body/{player}')

        await ctx.send(embed=embed)

    @commands.command(name='uuidtoname', aliases=['uuidtousername', 'uuid2name'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def uuid_to_username(self, ctx, uuid):
        """Turns a Minecraft uuid into a username"""

        with ctx.typing():
            res = await self.ses.get(f'https://api.mojang.com/user/profiles/{uuid}/names')

        if res.status == 204:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        jj = await res.json()

        try:
            name = jj[-1]['name']
        except KeyError:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        await self.bot.send(ctx, f'**{uuid}**: `{name}`')

    @commands.command(name='nametouuid', aliases=['usernametouuid', 'name2uuid'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def username_to_uuid(self, ctx, username):
        """Turns a Minecraft username into a Minecraft uuid"""

        with ctx.typing():
            res = await self.ses.post('https://api.mojang.com/profiles/minecraft', json=[username])

        jj = await res.json()

        if not jj or res.status == 204:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        uuid = jj[0]['id']

        await self.bot.send(ctx, f'**{username}**: `{uuid}`')

    @commands.command(name='nametoxuid', aliases=['grabxuid', 'benametoxuid'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def name_to_xuid(self, ctx, *, username):
        """Turns a Minecraft BE username/gamertag into an xuid"""

        with ctx.typing():
            res = await self.ses.get('https://floodgate-uuid.heathmitchell1.repl.co/uuid', params={'gamertag': username})

        text = await res.text()

        if 'User not found' in text or 'The UUID of' not in text:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        xuid = text.split()[-1]

        await self.bot.send(ctx, f'**{username}**: `{xuid}` / `{xuid[19:].replace("-", "").upper()}`')

    @commands.command(name='mccolors', aliases=['minecraftcolors', 'chatcolors', 'colorcodes'])
    async def color_codes(self, ctx):
        """Shows the Minecraft chat color codes"""

        embed = discord.Embed(color=self.d.cc, description=ctx.l.minecraft.mccolors.embed_desc)

        embed.set_author(name=ctx.l.minecraft.mccolors.embed_author_name)

        cs = ctx.l.minecraft.mccolors.formatting_codes

        embed.add_field(
            name=ctx.l.minecraft.mccolors.colors,
            value=f'<:red:697541699706028083> **{cs.red}** `§c`\n'
                  f'<:yellow:697541699743776808> **{cs.yellow}** `§e`\n'
                  f'<:green:697541699316219967> **{cs.green}** `§a`\n'
                  f'<:aqua:697541699173613750> **{cs.aqua}** `§b`\n'
                  f'<:blue:697541699655696787> **{cs.blue}** `§9`\n'
                  f'<:light_purple:697541699546775612> **{cs.light_purple}** `§d`\n'
                  f'<:white:697541699785719838> **{cs.white}** `§f`\n'
                  f'<:gray:697541699534061630> **{cs.gray}** `§7`\n'
        )

        embed.add_field(
            name=ctx.l.minecraft.mccolors.more_colors,
            value=f'<:dark_red:697541699488055426> **{cs.dark_red}** `§4`\n'
                  f'<:gold:697541699639050382> **{cs.gold}** `§6`\n'
                  f'<:dark_green:697541699500769420> **{cs.dark_green}** `§2`\n'
                  f'<:dark_aqua:697541699475472436> **{cs.dark_aqua}** `§3`\n'
                  f'<:dark_blue:697541699488055437> **{cs.dark_blue}** `§1`\n'
                  f'<:dark_purple:697541699437592666> **{cs.dark_purple}** `§5`\n'
                  f'<:dark_gray:697541699471278120> **{cs.dark_gray}** `§8`\n'
                  f'<:black:697541699496444025> **{cs.black}** `§0`\n'
        )

        embed.add_field(
            name=ctx.l.minecraft.mccolors.formatting,
            value=f'<:bold:697541699488186419> **{cs.bold}** `§l`\n'
                  f'<:strikethrough:697541699768942711> ~~{cs.strikethrough}~~ `§m`\n'
                  f'<:underline:697541699806953583> {cs.underline} `§n`\n'
                  f'<:italic:697541699152379995> *{cs.italic}* `§o`\n'
                  f'<:obfuscated:697541699769204736> ||{cs.obfuscated}|| `§k`\n'
                  f'<:reset:697541699697639446> {cs.reset} `§r`\n'
        )

        await ctx.send(embed=embed)

    @commands.command(name='buildidea', aliases=['idea'])
    async def build_idea(self, ctx):
        """Sends a random "build idea" which you could create"""

        prefix = random.choice(self.d.build_ideas['prefixes'])
        idea = random.choice(self.d.build_ideas['ideas'])

        await self.bot.send(ctx, f'{prefix} {idea}!')


def setup(bot):
    bot.add_cog(Minecraft(bot))
