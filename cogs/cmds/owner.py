from util.misc import recursive_update
from discord.ext import commands
from typing import Union
import classyjson as cj
import discord
import random
import ast
import sys
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
    async def eval_stuff(self, ctx, *, code):
        try:
            code_nice = f'async def eval_code():\n' + '\n'.join(f'    {i}' for i in code.strip(' `py\n ').splitlines())
            code_parsed = ast.parse(code_nice)
            code_final = code_parsed.body[0].body

            def insert_returns():
                if isinstance(code_final[-1], ast.Expr):
                    code_final[-1] = ast.Return(code_final[-1].value)
                    ast.fix_missing_locations(code_final[-1])

                if isinstance(code_final[-1], ast.If):
                    insert_returns(code_final[-1].body)
                    insert_returns(code_final[-1].orelse)

                if isinstance(code_final[-1], ast.With):
                    insert_returns(code_final[-1].body)

            insert_returns()

            env = {**locals(), **globals()}

            exec(compile(code_parsed, filename='<ast>', mode='exec'), env)
            result = (await eval(f'eval_code()', env))

            await ctx.send(f'```py\n{result}```')

        except discord.errors.Forbidden:
            await ctx.send('Missing permissions (FORBIDDEN)')
        except Exception as e:
            await self.bot.get_cog('Events').debug_error(ctx, e, ctx)

    @commands.command(name='gitpull')
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def gitpull(self, ctx):
        async with ctx.typing():
            os.system('sudo git pull > git_pull_log 2>&1')

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

            self.d.findables = cj.classify(self.d.special_findables + self.d.default_findables)
        elif thing.lower() == 'text':
            with open('data/text.json', 'r', encoding='utf8') as t:  # recursive shit not needed here
                self.bot.langs.update(cj.load(t))
        elif thing.lower() == 'mcservers':
            self.d.additional_mcservers = await self.db.fetch_all_mcservers()
        else:
            await self.bot.send(ctx, 'Invalid, options are "data", "text", or "mcservers"')
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

    @commands.command(name='setbal')
    @commands.is_owner()
    async def set_user_bal(self, ctx, user: Union[discord.User, int], balance: int):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, 'emeralds', balance)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name='itemwealth')
    @commands.is_owner()
    async def item_wealth(self, ctx):
        items = await self.db.db.fetch('SELECT * FROM items')

        users = {}

        for item in items:
            prev = users.get(item['uid'], 0)

            users[item['uid']] = prev + (item['amount'] * item['sell_price'])

        users = users.items()
        users_sorted = sorted(users, key=(lambda e: e[1]), reverse=True)[:30]

        body = ''
        for u in users_sorted:
            body += f'`{u[0]}` - {u[1]}{self.d.emojis.emerald}\n'

        await ctx.send(body)

    def get_mem_usage(self, obj, counted=None):
        mem_usage = 0

        if isinstance(obj, dict):
            for key, obj_child in obj.items():
                mem_usage += self.get_mem_usage(obj_child)

        if isinstance(obj, list):
            for obj_child in obj:
                mem_usage += self.get_mem_usage(obj_child)

        try:
            if counted is None:
                counted = []

            for key, obj_child in obj.__dict__.items():
                if hash(object_child) not in counted:
                    counted.append(hash(object_child))
                    mem_usage += self.get_mem_usage(obj_child, counted)
        except AttributeError:
            pass

        mem_usage += sys.getsizeof(obj)

        return mem_usage

    @commands.command(name='memusage', aliases=['memory', 'mem'])
    async def memory_usage(self, ctx, *, thing=None):
        mem_usage = {}

        if thing is None:
            for cog_name, cog in self.bot.cogs.items():
                for name, obj in cog.__dict__.items():
                    mem_usage[name] = self.get_mem_usage(obj) / 1000000 # mb
        else:
            thing = eval(thing)

            if isinstance(thing, dict):
                for name, obj in thing.items():
                    mem_usage[name] = self.get_mem_usage(obj) / 1000000
            elif isinstance(thing, list):
                for i, obj in enumerate(thing):
                    mem_usage[i] = self.get_mem_usage(obj) / 1000000
            else:
                try:
                    for name, obj in thing.__dict__.items():
                        mem_usage[name] = self.get_mem_usage(obj) / 1000000
                except AttributeError:
                    mem_usage['thing'] = self.get_mem_usage(thing) / 1000000

        mem_usage_sorted = sorted(mem_usage.items(), key=(lambda t: t[1]), reverse=True)[:25]

        body = ''

        for name, value in mem_usage_sorted:
            body += f'{name}: {value} mb\n'

        await ctx.send(body)

    """
    @commands.command(name='updatesticky')
    @commands.is_owner()
    async def update_sticky(self, ctx):
        await ctx.send('starting...')

        to_be_sticky = [
            *self.d.mining.pickaxes,
            'Netherite Sword', 'Diamond Sword', 'Gold Sword', 'Iron Sword', 'Stone Sword', 'Wood Sword',
            'Bane Of Pillagers Amulet',
            'Rich Person Tropy'
        ]

        for item in to_be_sticky:
            await self.db.db.execute('UPDATE items SET sticky = true WHERE name = $1', item)

        await ctx.send('done.')
    """

    """
    @commands.command(name='massunban')
    @commands.is_owner()
    async def mass_unban(self, ctx):
        exempt = [m.id for m in self.bot.get_guild(730519472863051910).members]

        # remove botbans
        async with self.db.db.acquire() as con:
            await con.execute('UPDATE users SET bot_banned = false WHERE uid = ANY($1::bigint[])', exempt)

        await ctx.send('Finished bot-bans.')

        support_guild = self.bot.get_guild(self.d.support_server_id)

        # server bans
        bans = await support_guild.bans()
        for ban in bans:
            if ban.user.id not in exempt:
                user = self.bot.get_user(ban.user.id)

                if user is None:
                    try:
                        user = await self.bot.fetch_user(ban.user.id)
                    except Exception:
                        continue

                await support_guild.unban(user, reason='Mass pardon of Nov 14th')

        await ctx.send('Done guild unbanning.')

        for uid in exempt:
            await self.bot.get_cog('Mod').ban_user(ctx, uid, reason='Llama Alt')

        await ctx.send('Done restoring llama bans')
    """


def setup(bot):
    bot.add_cog(Owner(bot))
