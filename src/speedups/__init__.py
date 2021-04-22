import discord

import speedups.gateway as gateway


def install():
    discord.gateway.GatewayRatelimiter = gateway.GatewayRatelimiter
    discord.gateway.DiscordWebSocket = gateway.DiscordWebSocket
