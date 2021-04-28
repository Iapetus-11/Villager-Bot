"""Much of the code in this folder is from github.com/Rapptz/discord.py, credit is to the author of discord.py"""

import sys

import speedups.mixins
import speedups.gateway
import speedups.activity
import speedups.utils
import speedups.message

import speedups.ext.commands.cooldowns as speedups_cooldowns


def install():
    discord_module = sys.modules.get("discord")

    for module in (speedups.mixins, speedups.gateway, speedups.activity, speedups.utils, speedups.message):
        for thing in module.__all__:
            if hasattr(discord_module, thing):
                setattr(discord_module, thing, getattr(module, thing))

    for module in (speedups_cooldowns,):
        for thing in module.__all__:
            if hasattr(discord_module.ext.commands.cooldowns, thing):
                setattr(discord_module.ext.commands.cooldowns, thing, getattr(module, thing))
