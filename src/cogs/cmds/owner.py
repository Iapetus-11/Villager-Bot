from util.misc import recursive_update
from discord.ext import commands
from typing import Union
import functools
import aiofiles
import asyncio
import discord
import random
import arrow
import json
import ast
import os

import util.cj as cj


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.db = bot.get_cog("Database")

    @commands.command(name="load")
    @commands.is_owner()
    async def load_cog(self, ctx, cog):
        self.bot.load_extension(f"cogs.{cog}")
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload_cog(self, ctx, cog):
        self.bot.unload_extension(f"cogs.{cog}")
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx, cog):
        if cog == "all":
            await self.reload_all_cogs(ctx)
        else:
            self.bot.reload_extension(f"cogs.{cog}")
            await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="reloadall")
    @commands.is_owner()
    async def reload_all_cogs(self, ctx):
        for cog in self.bot.cog_list:
            self.bot.reload_extension(cog)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="eval")
    @commands.is_owner()
    async def eval_stuff(self, ctx, *, code):
        if code.startswith("```"):
            code = code.lstrip(" `py\n ").rstrip(" `\n ")

        code_nice = "async def eval_code():\n" + "\n".join(f"    {i}" for i in code.splitlines())
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

        try:
            exec(compile(code_parsed, filename="<ast>", mode="exec"), env)
            result = await eval("eval_code()", env)
        except discord.errors.Forbidden:
            await ctx.send("Missing permissions (FORBIDDEN)")
        except Exception as e:
            await self.bot.get_cog("Events").debug_error(ctx, e, ctx)
        else:
            await ctx.send(f"```py\n{result}```")

    @commands.command(name="gitpull")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def gitpull(self, ctx):
        async with ctx.typing():
            system_call = functools.partial(os.system, "git pull > git_pull_log 2>&1")
            await self.bot.loop.run_in_executor(self.bot.tpool, system_call)

            async with aiofiles.open("git_pull_log", "r") as f:
                await self.bot.send(ctx, f"```diff\n{await f.read()}\n```")

        os.remove("git_pull_log")

    @commands.command(name="update")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=True)
    @commands.is_owner()
    async def update(self, ctx, thing):
        if thing.lower() == "data":
            async with aiofiles.open("data/data.json", "r", encoding="utf8") as d:
                self.d = recursive_update(self.d, cj.classify(json.loads(await d.read())))

            # update some thing swhich were just overwritten
            self.bot.populate_null_data_values()
        elif thing.lower() == "text":
            async with aiofiles.open("data/text.json", "r", encoding="utf8") as t:  # recursive shit not needed here
                self.bot.langs.update(self.d, cj.classify(json.loads(await t.read())))
        elif thing.lower() == "mcservers":
            self.d.additional_mcservers = await self.db.fetch_all_mcservers()
        else:
            await self.bot.send(ctx, 'Invalid, options are "data", "text", or "mcservers"')
            return

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="botban")
    @commands.is_owner()
    async def botban_user(self, ctx, users: commands.Greedy[discord.User]):
        if len(users) == 0:
            await self.bot.send(ctx, "You have to specify a user.")
            return

        for user in users:
            await self.db.set_botbanned(user.id, True)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="unbotban", aliases=["botunban"])
    @commands.is_owner()
    async def unbotban_user(self, ctx, users: commands.Greedy[discord.User]):
        if len(users) == 0:
            await self.bot.send(ctx, "You have to specify a user.")
            return

        for user in users:
            await self.db.set_botbanned(user.id, False)

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="lookup")
    @commands.is_owner()
    async def lookup(self, ctx, user: Union[discord.User, int]):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        guilds = ""

        for guild in self.bot.guilds:
            if guild.get_member(uid) is not None:
                guilds += f"{guild} **|** `{guild.id}`\n"

        if guilds == "":
            await self.bot.send(ctx, "No results...")
        else:
            await self.bot.send(ctx, guilds)

    @commands.command(name="givehistory", aliases=["transactions"])
    @commands.is_owner()
    async def transaction_history(self, ctx, user: discord.User):
        page_max = await self.db.fetch_transactions_page_count(user.id)
        page = 0

        msg = None
        first_time = True

        while True:
            entries = await self.db.fetch_transactions_page(user.id, page=page)

            if len(entries) == 0:
                body = ctx.l.econ.inv.empty
            else:
                body = ""  # text for that page

                for entry in entries:
                    giver = self.bot.get_user(entry["giver_uid"])
                    receiver = self.bot.get_user(entry["recvr_uid"])
                    item = entry["item"]

                    if item == "emerald":
                        item = self.d.emojis.emerald

                    body += f"__[{giver}]({entry['giver_uid']})__ *gave* __{entry['amount']}x **{item}**__ *to* __[{receiver}]({entry['recvr_uid']})__ *{arrow.get(entry['ts']).humanize()}*\n"

                embed = discord.Embed(color=self.d.cc, description=body)
                embed.set_author(name=f"Transaction history for {user}", icon_url=user.avatar_url_as())
                embed.set_footer(text=f"Page {page+1}/{page_max+1}")

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

            if page_max > 0:
                if first_time:
                    await msg.add_reaction("⬅️")
                    await asyncio.sleep(0.1)
                    await msg.add_reaction("➡️")
                    await asyncio.sleep(0.1)

                try:

                    def author_check(react, r_user):
                        return r_user == ctx.author and ctx.channel == react.message.channel and msg.id == react.message.id

                    react, r_user = await self.bot.wait_for(
                        "reaction_add", check=author_check, timeout=(3 * 60)
                    )  # wait for reaction from message author
                except asyncio.TimeoutError:
                    return

                await react.remove(ctx.author)

                if react.emoji == "⬅️":
                    page -= 1 if page - 1 >= 0 else 0
                if react.emoji == "➡️":
                    page += 1 if page + 1 <= page_max else 0

                await asyncio.sleep(0.1)
            else:
                break

            first_time = False

    @commands.command(name="setactivity")
    @commands.is_owner()
    async def set_activity(self, ctx, *, activity):
        await self.bot.change_presence(activity=discord.Game(name=activity))

        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="whoyadaddy", aliases=["whodaddy"])
    @commands.is_owner()
    async def who_ya_daddy(self, ctx):
        await ctx.send(f"Iapetus11 is {random.choice(self.d.owos)}")

    @commands.command(name="topguilds")
    @commands.is_owner()
    async def top_guilds(self, ctx):
        guilds = sorted(self.bot.guilds, reverse=True, key=(lambda g: g.member_count))[:20]

        body = ""
        for i, g in enumerate(guilds, start=1):
            body += f"{i}. **{g.member_count}** {g} *{g.id}*\n"

        await self.bot.send(ctx, body)

    @commands.command(name="toggleownerlock", aliases=["ownerlock"])
    @commands.is_owner()
    async def toggle_owner_lock(self, ctx):
        self.bot.owner_locked = not self.bot.owner_locked
        await self.bot.send(ctx, f"All commands owner only: {self.bot.owner_locked}")

    @commands.command(name="setbal")
    @commands.is_owner()
    async def set_user_bal(self, ctx, user: Union[discord.User, int], balance: int):
        if isinstance(user, discord.User):
            uid = user.id
        else:
            uid = user

        await self.db.update_user(uid, "emeralds", balance)
        await ctx.message.add_reaction(self.d.emojis.yes)

    @commands.command(name="itemwealth")
    @commands.is_owner()
    async def item_wealth(self, ctx):
        items = await self.db.db.fetch("SELECT * FROM items")

        users = {}

        for item in items:
            prev = users.get(item["uid"], 0)

            users[item["uid"]] = prev + (item["amount"] * item["sell_price"])

        users = users.items()
        users_sorted = sorted(users, key=(lambda e: e[1]), reverse=True)[:30]

        body = ""
        for u in users_sorted:
            body += f"`{u[0]}` - {u[1]}{self.d.emojis.emerald}\n"

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
