"""Much of the code in this folder is from github.com/Rapptz/discord.py, credit is to the author of discord.py"""

import sys

# fully reimplemented
import speedups.gateway
import speedups.mixins

# partial implementations
import speedups.activity
import speedups.message
import speedups.utils


def install():
    discord_module = sys.modules.get("discord")

    for module in (speedups.activity, speedups.message, speedups.utils, speedups.gateway, speedups.mixins):
        for thing in module.__all__:
            if hasattr(discord_module, thing):
                setattr(discord_module, thing, getattr(module, thing))
