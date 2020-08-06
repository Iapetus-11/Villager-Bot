import aiohttp
import base64
import discord
import json
from discord.ext import commands


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog('Database')

        self.ses = aiohttp.ClientSession(loop=self.bot.loop)

    @commands.command(name='mcping', aliases=['mcstatus'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def mcping(self, ctx, host=None, port: int = None):
        """Checks the status of a given Minecraft server"""

        if host is None:
            combined = await self.db.fetch_default_server(ctx.guild.id)
            if combined is None:
                await self.bot.send(ctx,
                                    f'To use this shortcut, you must set a default Minecraft server via `{ctx.prefix}config`')
        else:
            port_str = ''
            if port is not None:
                port_str = f':{port}'
            combined = f'{host}{port_str}'

        async with ctx.typing():
            async with self.ses.get(f'https://theapi.info/mc?host={combined}') as res:  # fetch status from api
                jj = await res.json()

        if jj['online'] is not True:
            embed = discord.Embed(color=self.bot.cc, title=f'<:b:730460448197050489> {combined} is offline')
            await ctx.send(embed=embed)
            return

        player_list = jj['players_names']  # list
        players_online = jj['players_online']  # int

        embed = discord.Embed(color=self.bot.cc, title=f'<:a:730460448339525744> {combined} is online')
        # should probably set thumbnail to server favicon or add image from theapi.info/mc/mcpingimg

        embed.add_field(name='Latency/Ping', value=jj['latency'])
        embed.add_field(name='Version', value=jj['version']['brand'])

        player_list_cut = player_list[:32]

        if jj['version']['method'] != 'query' and len(player_list_cut) < 1:
            player_list_cut = ['Player list is not available for this server...']
        elif len(player_list_cut) < players_online:
            player_list_cut.append(f'and {players_online - len(player_list_cut)} others...')

        embed.add_field(
            name=f'Online Players ({players_online}/{jj["players_max"]})',
            value=discord.utils.escape_markdown(','.join(player_list_cut)),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name='stealskin', aliases=['getskin', 'skin', 'mcskin'])
    @commands.cooldown(1, 2.5, commands.BucketType.user)
    async def steal_skin(self, ctx, player):
        """'steals' the skin of a Minecraft player"""

        async with ctx.typing():
            res = await self.ses.get(f'https://api.mojang.com/users/profiles/minecraft/{player}')

        if res.status == 204:
            await self.bot.send(ctx, 'That player is invalid or doesn\'t exist.')
            return

        uuid = await res.json().get('id')

        if uuid is None:
            await self.bot.send(ctx, 'That player is invalid or doesn\'t exist.')
            return

        res_profile = await self.ses.get(
            f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}?unsigned=false'
        )
        profile_content = await res_profile.json()

        if 'error' in profile_content or len(content['properties']) == 0:
            await self.bot.send(ctx, 'Oops, something went wrong while fetching that player\'s profile.')
            return

        try:
            decoded_jj = json.loads(base64.b64decode(content['properties'][0]['value']))
            skin_url = decoded_jj['textures']['SKIN']['url']
        except Exception:
            await self.bot.send(ctx, 'Oops, something went wrong while fetching that player\'s profile.')
            return

        embed = discord.Embed(color=self.bot.cc, description=f'{gamertag}\'s skin\n[**[Download]**]({skin_url})')
        embed.set_thumbnail(url=skin_url)
        embed.set_image(url=f'https://mc-heads.net/body/{gamertag}')

        await ctx.send(embed=embed)

    @commands.command(name='uuidtoname', aliases=['uuidtousername', 'uuid2name'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def uuid_to_username(self, ctx, uuid):
        """Turns a Minecraft uuid into a username"""

        res = await self.ses.get(f'https://api.mojang.com/user/profiles/{uuid}/names')

        if res.status == 204:
            await self.bot.send(ctx, 'That player is invalid or doesn\'t exist.')
            return

        jj = await response.json()
        name = jj[len(j) - 1]['name']

        await self.bot.send(ctx, f'**{uuid}**: `{name}`')

    @commands.command(name='nametouuid', aliases=['usernametouuid', 'name2uuid'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def username_to_uuid(self, ctx, username):
        """Turns a Minecraft username into a Minecraft uuid"""

        res = await self.ses.post('https://api.mojang.com/profiles/minecraft', json=[username])
        jj = await res.json()

        if not jj or res.status == 204:
            await self.bot.send(ctx, 'That player is invalid or doesn\'t exist.')
            return

        uuid = jj[0]['id']

        await self.bot.send(ctx, f'**{gamertag}**: `{uuid}`')

    @commands.command(name='mccolors', aliases=['minecraftcolors', 'chatcolors', 'colorcodes'])
    async def color_codes(self, ctx):
        """Shows the Minecraft chat color codes"""

        embed = discord.Embed(
            color=await self.bot.cc(ctx.author.id),
            description='Text in Minecraft can be formatted using different codes and\nthe section (`§`) sign.'
        )

        embed.set_author(name='Minecraft Formatting Codes')

        embed.add_field(
            name='Color Codes',
            value='<:red:697541699706028083> **Red** `§c`\n'
                  '<:yellow:697541699743776808> **Yellow** `§e`\n'
                  '<:green:697541699316219967> **Green** `§a`\n'
                  '<:aqua:697541699173613750> **Aqua** `§b`\n'
                  '<:blue:697541699655696787> **Blue** `§9`\n'
                  '<:light_purple:697541699546775612> **Light Purple** `§d`\n'
                  '<:white:697541699785719838> **White** `§f`\n'
                  '<:gray:697541699534061630> **Gray** `§7`\n'
        )

        embed.add_field(
            name='Color Codes',
            value='<:dark_red:697541699488055426> **Dark Red** `§4`\n'
                  '<:gold:697541699639050382> **Gold** `§6`\n'
                  '<:dark_green:697541699500769420> **Dark Green** `§2`\n'
                  '<:dark_aqua:697541699475472436> **Dark Aqua** `§3`\n'
                  '<:dark_blue:697541699488055437> **Dark Blue** `§1`\n'
                  '<:dark_purple:697541699437592666> **Dark Purple** `§5`\n'
                  '<:dark_gray:697541699471278120> **Dark Gray** `§8`\n'
                  '<:black:697541699496444025> **Black** `§0`\n'
        )

        embed.add_field(
            name='Formatting Codes',
            value='<:bold:697541699488186419> **Bold** `§l`\n'
                  '<:strikethrough:697541699768942711> ~~Strikethrough~~ `§m`\n'
                  '<:underline:697541699806953583> __Underline__ `§n`\n'
                  '<:italic:697541699152379995> *Italic* `§o`\n'
                  '<:obfuscated:697541699769204736> ||Obfuscated|| `§k`\n'
                  '<:reset:697541699697639446> Reset `§r`\n'
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Minecraft(bot))
