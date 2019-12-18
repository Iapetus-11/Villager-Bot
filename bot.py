from discord.ext import commands
import discord
from os import system
import json

#set window title
#system("title Minecraft Translator Discord Bot")

bot = commands.Bot(command_prefix='!!', help_command=None, case_insensitive=True)
cogs = ["cmds", "events", "owner", "msgs",
        "admincmds", "currency", "loops"]

#load cogs in cogs list
for cog in cogs:
    bot.load_extension("cogs."+cog)

@bot.check
async def stay_safe(ctx):
    return ctx.message.author.id is not 639498607632056321 and not ctx.message.author.bot and bot.is_ready()

#actually start bot
key = json.load(open("keys.json", "r"))["discord"]
bot.run(key, bot=True)