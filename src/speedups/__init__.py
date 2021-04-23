import discord

import speedups._gateway as gateway


def install():
    discord.gateway = gateway
