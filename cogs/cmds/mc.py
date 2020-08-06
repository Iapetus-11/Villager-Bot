import aiohttp
import discord
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


def setup(bot):
    bot.add_cog(Minecraft(bot))
