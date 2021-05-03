"""Much of the code in this folder is from github.com/Rapptz/discord.py, credit is to the author of discord.py"""

import importlib
import sys

import speedups.mixins
import speedups.gateway
import speedups.activity
import speedups.utils
import speedups.message

import speedups.ext.commands.cooldowns as speedups_cooldowns

import speedups.ext.commands.view as speedups_view


def install_module(new_module, old_module):
    for thing in new_module.__all__:
        if hasattr(old_module, thing):
            setattr(old_module, thing, getattr(new_module, thing))


def install():
    discord = sys.modules.get("discord")

    for new_module in (speedups.mixins, speedups.gateway, speedups.activity, speedups.utils, speedups.message):
        install_module(new_module, discord)

    install_module(speedups_cooldowns, discord.ext.commands.cooldowns)
    install_module(speedups_view, discord.ext.commands.view)
    
    importlib.reload(discord.ext.commands.bot)
