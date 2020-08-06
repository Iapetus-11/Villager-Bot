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
        embed.set_image(url=f"https://mc-heads.net/body/{gamertag}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Minecraft(bot))
