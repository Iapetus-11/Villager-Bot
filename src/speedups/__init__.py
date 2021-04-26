"""Much of the code in this folder is from github.com/Rapptz/discord.py, credit is to the author of discord.py"""

import sys

import speedups.mixins
import speedups.gateway
import speedups.activity
import speedups.utils
import speedups.message


def install():
    discord_module = sys.modules.get("discord")

    for module in (speedups.mixins, speedups.gateway, speedups.activity, speedups.utils, speedups.message):
        for thing in module.__all__:
            if hasattr(discord_module, thing):
                setattr(discord_module, thing, getattr(module, thing))
