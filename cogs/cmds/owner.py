from util.misc import recursive_update
from discord.ext import commands
from typing import Union
import classyjson as cj
import discord
import random
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
        if cog == 'all':
            await self.reload_all_cogs(ctx)
        else:
            self.bot.reload_extension(f'cogs.{cog}')
            await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='reloadall')
    @commands.is_owner()
    async def reload_all_cogs(self, ctx):
        for cog in self.bot.cog_list:
            self.bot.reload_extension(cog)

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
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def gitpull(self, ctx):
        async with ctx.typing():
            os.system('git pull > git_pull_log 2>&1')

        with open('git_pull_log', 'r') as f:
            await self.bot.send(ctx, f'```diff\n{f.read()}\n```')

        os.remove('git_pull_log')

    @commands.command(name='update')
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def update(self, ctx, thing):
        if thing.lower() == 'data':
            with open('data/data.json', 'r', encoding='utf8') as d:
                self.d = recursive_update(self.d, cj.load(d))
        elif thing.lower() == 'text':
            with open('data/text.json', 'r', encoding='utf8') as t:  # recursive shit not needed here
                self.bot.langs.update(cj.load(t))
        else:
            await self.bot.send(ctx, 'Invalid, options are "data" or "text"')
            return

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='botban')
    @commands.is_owner()
    async def botban_user(self, ctx, users: commands.Greedy[discord.User]):
        if len(users) == 0:
            await self.bot.send(ctx, 'You have to specify a user.')
            return

        for user in users:
            await self.db.set_botbanned(user.id, True)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='unbotban', aliases=['botunban'])
    @commands.is_owner()
    async def unbotban_user(self, ctx, users: commands.Greedy[discord.User]):
        if len(users) == 0:
            await self.bot.send(ctx, 'You have to specify a user.')
            return

        for user in users:
            await self.db.set_botbanned(user.id, False)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='lookup')
    @commands.is_owner()
    async def lookup(self, ctx, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        guilds = ''

        for guild in self.bot.guilds:
            if guild.get_member(uid) is not None:
                guilds += f'{guild} **|** `{guild.id}`\n'

        if guilds == '':
            await self.bot.send(ctx, 'No results...')
        else:
            await self.bot.send(ctx, guilds)

    @commands.command(name='setactivity')
    @commands.is_owner()
    async def set_activity(self, ctx, *, activity):
        await self.bot.change_presence(activity=discord.Game(name=activity))

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='whoyadaddy', aliases=['whodaddy'])
    @commands.is_owner()
    async def who_ya_daddy(self, ctx):
        await ctx.send(f'Iapetus11 is {random.choice(self.d.owos)}')

    @commands.command(name='topguilds')
    @commands.is_owner()
    async def top_guilds(self, ctx):
        guilds = sorted(self.bot.guilds, reverse=True, key=(lambda g: g.member_count))[:20]

        body = ''
        for i, g in enumerate(guilds, start=1):
            body += f'{i}. **{g.member_count}** {g} *{g.id}*\n'

        await self.bot.send(ctx, body)

    @commands.command(name='toggleownerlock', aliases=['ownerlock'])
    @commands.is_owner()
    async def toggle_owner_lock(self, ctx):
        self.bot.owner_locked = not self.bot.owner_locked
        await self.bot.send(ctx, f'All commands owner only: {self.bot.owner_locked}')


def setup(bot):
    bot.add_cog(Owner(bot))
