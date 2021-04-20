from discord.ext import commands
import statcord


class StatCord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.statcord_client = statcord.Client(bot, bot.k.statcord, custom1=self.get_vote_count, custom2=self.get_error_count)
        self.statcord_client.start_loop()

        self.vote_count = 0
        self.error_count = 0

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.statcord_client.command_run(ctx)

    @commands.Cog.listener()
    async def on_topgg_event(self, data):
        if data.type == "upvote":
            self.vote_count += 1

    async def get_vote_count(self):
        vote_count = self.vote_count
        self.vote_count = 0
        return vote_count

    async def get_error_count(self):
        error_count = self.error_count
        self.error_count = 0
        return str(error_count)


def setup(bot):
    bot.add_cog(StatCord(bot))
