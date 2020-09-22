import aiohttp
import base64
import discord
import json
import random
from discord.ext import commands


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.d = self.bot.d

        self.db = self.bot.get_cog('Database')

        self.ses = aiohttp.ClientSession(loop=self.bot.loop)

    def cog_unload(self):
        self.bot.loop.create_task(self.ses.close())

    @commands.command(name='mcping', aliases=['mcstatus'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def mcping(self, ctx, host=None, port: int = None, note: str = None):
        """Checks the status of a given Minecraft server"""

        if host is None:
            combined = await self.db.fetch_default_server(ctx.guild.id)
            if combined is None:
                await self.bot.send(ctx, ctx.l.minecraft.mcping.shortcut_error.format(ctx.prefix))
        else:
            port_str = ''
            if port is not None:
                port_str = f':{port}'
            combined = f'{host}{port_str}'

        async with ctx.typing():
            async with self.ses.get(f'https://betterapi.net/mc/mcping?host={combined}&k={self.d.k}') as res:  # fetch status from api
                jj = await res.json()

        if not jj['success'] or not jj['online']:
            embed = discord.Embed(color=self.d.cc, title=ctx.l.minecraft.mcping.title_offline.format(self.d.emojis.offline, combined))
            await ctx.send(embed=embed)
            return

        player_list = jj.get('players_names', [])  # list
        if player_list is None:
            player_list = []

        players_online = jj['players_online']  # int

        embed = discord.Embed(color=self.d.cc, title=ctx.l.minecraft.mcping.title_online.format(self.d.emojis.online, combined))
        # should probably set thumbnail to server favicon or add image from betterapi.net:6400/mc/mcpingimg

        embed.add_field(name=ctx.l.minecraft.mcping.latency, value=jj['latency'])
        embed.add_field(name=ctx.l.minecraft.mcping.version, value=jj['version'].get('brand', 'Unknown'))

        player_list_cut = player_list[:24]

        if jj['version']['method'] != 'query' and len(player_list_cut) < 1:
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

        embed.set_image(url=f'https://betterapi.net/mc/mcpingimg?host={combined}&imgonly=true&v={random.random()*100000}&k={self.d.k}')

        if jj['favicon'] is not None:
            embed.set_thumbnail(url=f'https://betterapi.net/mc/serverfavi?host={combined}&k={self.d.k}')

        if ctx.command.name == 'randommc':
            if note is not None:
                embed.set_footer(text=note)

        await ctx.send(embed=embed)

    @commands.command(name='randommc', aliases=['randommcserver', 'randomserver'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def random_mc_server(self, ctx):
        s = await self.db.fetch_random_server()
        await self.mcping(ctx, s['address'], s['port'], s['note'])

    @commands.command(name='stealskin', aliases=['getskin', 'skin', 'mcskin'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def steal_skin(self, ctx, player):
        """"steals" the skin of a Minecraft player"""

        async with ctx.typing():
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

        res = await self.ses.get(f'https://api.mojang.com/user/profiles/{uuid}/names')

        if res.status == 204:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        jj = await res.json()
        name = jj[len(jj) - 1]['name']

        await self.bot.send(ctx, f'**{uuid}**: `{name}`')

    @commands.command(name='nametouuid', aliases=['usernametouuid', 'name2uuid'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def username_to_uuid(self, ctx, username):
        """Turns a Minecraft username into a Minecraft uuid"""

        res = await self.ses.post('https://api.mojang.com/profiles/minecraft', json=[username])
        jj = await res.json()

        if not jj or res.status == 204:
            await self.bot.send(ctx, ctx.l.minecraft.invalid_player)
            return

        uuid = jj[0]['id']

        await self.bot.send(ctx, f'**{username}**: `{uuid}`')

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
