from discord.ext import commands
import classyjson
import discord


class Useful(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        #self.help_texts = classyjson.loads('{}')  # creates an empty NiceDict ~~bro~~
        self.help_texts = classyjson.NiceDict()

    @commands.Cog.listener()
    async def on_ready(self):
        for cog in ('Econ', 'Fun', 'Minecraft', 'Mod'):
            self.help_texts[cog] = await self.conglomerate(self.bot.get_cog(cog))

    async def conglomerate(self, cog):
        cmds = cog.get_commands()
        body = ''

        for cmd in cmds:
            print(cmd.clean_params)
            if cmd.enabled and not cmd.hidden:
                body += '\n`{0}' + f'{cmd.name} {cmd.usage} {cmd.short_doc}`'

        return body

    @commands.group(name='help')
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed()
            p = ctx.prefix

            embed.add_field(name='Minecraft', value=f'{p}help mc')
            embed.add_field(name='\uFEFF', value='\uFEFF')
            embed.add_field(name='Fun', value=f'{p}help fun')

            embed.add_field(name='\uFEFF', value='\uFEFF')
            embed.add_field(name='Economy', value=f'{p}help econ')
            embed.add_field(name='\uFEFF', value='\uFEFF')

            embed.add_field(name='Useful', value=f'{p}help useful')
            embed.add_field(name='\uFEFF', value='\uFEFF')
            embed.add_field(name='Admin', value=f'{p}help admin')

            await ctx.send(embed=embed)

    @help.command(name='minecraft', aliases=['mc'])
    async def help_minecraft(self, ctx):
        embed = discord.Embed(
            description='Need more help? Found a bug? Join the official [support server]({self.bot.d.support})!\n\uFEFF',
            title='Minecraft Commands'
        )

        embed.description += self.help_texts.Minecraft.format(ctx.prefix)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful(bot))
