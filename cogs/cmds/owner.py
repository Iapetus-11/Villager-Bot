from discord.ext import commands
import discord
import os


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.db = self.bot.get_cog('Database')

        self.d = self.bot.d

    @commands.command(name='load')
    @commands.is_owner()
    async def load_cog(self, ctx, cog):
        self.bot.load_extension(f'cogs.{cog}')
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='unload')
    @commands.is_owner()
    async def unload_cog(self, ctx, cog):
        self.bot.unload_extension(f'cogs.{cog}')
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cog(self, ctx, cog):
        self.bot.reload_extension(f'cogs.{cog}')
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='eval')
    @commands.is_owner()
    async def eval_stuff(self, ctx, *, stuff):
        await ctx.send(f'```{eval(stuff)}```')

    @commands.command(name='exec')
    @commands.is_owner()
    async def exec_stuff(self, ctx, *, stuff):
        await ctx.send(f'```{exec(stuff)}```')

    @commands.command(name='awaiteval')
    @commands.is_owner()
    async def await_eval_stuff(self, ctx, *, stuff):
        await ctx.send(f'```{await eval(stuff)}```')

    @commands.command(name='gitpull')
    @commands.is_owner()
    async def gitpull(self, ctx):
        os.system('git pull > git_pull_log 2>&1')

        with open('git_pull_log', 'r') as f:
            await self.bot.send(ctx, f'```diff\n{f.read()}\n```')

        os.remove('git_pull_log')

    @commands.command(name='botban')
    @commands.is_owner()
    async def botban_user(self, ctx, users: commands.Greedy[discord.User]):
        if len(users) == 0:
            await self.bot.send('You have to specify a user.')
            return

        for user in users:
            await self.db.set_botbanned(user.id, True)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='unbotban', aliases=['botunban'])
    @commands.is_owner()
    async def unbotban_user(self, ctx, users: commands.Greedy[discord.User]):
        if len(users) == 0:
            await self.bot.send('You have to specify a user.')
            return

        for user in users:
            await self.db.set_botbanned(user.id, False)

        await ctx.message.add_reaction(self.d.emojis.yes)


def setup(bot):
    bot.add_cog(Owner(bot))
