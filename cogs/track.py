from discord.ext import commands, tasks
import discord
import json
import psycopg2

class Track(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("keys.json", "r") as k:
            keys = json.load(k)
        self.db = psycopg2.connect(host="localhost",database="villagerbot", user="pi", password=keys["postgres"])
        self.save.start()
        
    @tasks.loop(seconds=2)
    async def save(self):
        self.db.commit()
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.clean_content.startswith("!!"):
            cur = self.db.cursor()
            cur.execute("SELECT * FROM tracker WHERE tracker.gid='"+str(message.channel.guild.id)+"'")
            val = cur.fetchone()
            if val is None:
                cur.execute("INSERT INTO tracker VALUES ('"+str(message.channel.guild.id)+"', '1')")
            else:
                cc = int(val[1])+1
                cur.execute("UPDATE tracker SET cc='"+str(cc)+"' WHERE gid='"+str(message.channel.guild.id)+"'")

    @commands.command(name="stats")
    @commands.is_owner()
    async def statsList(self, ctx):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM tracker")
        joe = cur.fetchall()
        topps = [(18397410834738, -1)]
        for trak in joe: #sort
            if int(trak[1]) > int(topps[0][1]):
                topps.insert(0, trak)
        i = 0
        for top in topps:
            if i >= 5:
                return
            await ctx.send("*"+str(top[0])+"*   **"+str(top[1])+"**")
            i+=1
    
def setup(bot):
    bot.add_cog(Track(bot))
