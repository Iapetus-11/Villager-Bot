import discord

import speedups.gateway as gateway
import speedups.mixins as mixins


def install():
    discord.gateway = gateway
    discord.mixins = mixins
