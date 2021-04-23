import discord

import speedups.gateway as gateway


def install():
    discord.gateway = gateway
