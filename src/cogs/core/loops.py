from discord.ext import commands, tasks
import traceback
import discord
import random


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.d = bot.d

        self.db = bot.get_cog("Database")

        self.change_status.start()
        self.update_fishing_prices.start()
        self.remind_reminders.start()

    def cog_unload(self):
        self.change_status.cancel()
        self.update_fishing_prices.cancel()
        self.remind_reminders.cancel()

    @tasks.loop(minutes=45)
    async def change_status(self):
        await self.bot.wait_until_ready()
        await self.bot.change_presence(activity=discord.Game(name=random.choice(self.d.playing_list)))

    @tasks.loop(hours=24)
    async def update_fishing_prices(self):
        self.bot.update_fishing_prices()

    async def remind(self, reminder):
        channel = self.bot.get_channel(reminder["cid"])

        if channel is not None:
            user = self.bot.get_user(reminder["uid"])

            if user is not None:
                lang = self.bot.get_lang(channel)

                try:
                    await channel.fetch_message(reminder["mid"]).reply(
                        lang.useful.remind.reminder.format(user.mention, reminder["reminder"]), mention_author=True
                    )
                except Exception:
                    try:
                        await channel.send(lang.useful.remind.reminder.format(user.mention, reminder["reminder"]))
                    except Exception as e:
                        traceback_text = "".join(traceback.format_exception(type(e), e, e.__traceback__, 4))
                        await self.bot.send(
                            self.bot.get_channel(self.d.error_channel_id), f"Reminder error: {user} ```{traceback_text}```"
                        )

    @tasks.loop(seconds=15)
    async def remind_reminders(self):
        for reminder in await self.db.fetch_current_reminders():
            self.bot.loop.create_task(self.remind(reminder))


def setup(bot):
    bot.add_cog(Loops(bot))
