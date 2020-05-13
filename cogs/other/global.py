from discord.ext import commands
import discord
import arrow
import json


class Global(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Stats command stuffs
        self.msg_count = 0
        self.cmd_count = 0
        self.cmd_vect = [0, 0]
        self.vote_count = 0
        self.vote_vect = [0, 0]

        self.startTime = arrow.utcnow()

        self.enchantLang = {"a": "\u1511", "b": "\u0296", "c": "\u14f5", "d": "\u21b8", "e": "\u14b7",
                            "f": "\u2393", "g": "\u22a3", "h": "\u2351", "i": "\u254e", "Ｊ": "\u22ee",
                            "k": "\ua58c", "l": "\ua58e", "m": "\u14b2", "n": "\u30ea", "o": "o", "p": "\u203c",
                            "q": "\u1451", "r": "\u2237", "s": "\u14ed", "t": "\u2138", "u": "\u268d",
                            "v": "\u234a", "w": "\u2234", "x": "\u0307", "y": "‖", "z": "\u2a05"}

        self.villagerLang = {"a": "hruh", "b": "hur", "c": "hurgh", "d": "hdur", "e": "mreh", "f": "hrgh",
                             "g": "hg", "h": "hhh", "i": "ehr", "j": "hrg", "k": "hregh", "l": "hrmg",
                             "m": "hrmm", "n": "hmeh", "o": "hugh", "p": "hrum", "q": "huerhg", "r": "hrrrh",
                             "s": "surgghm", "t": "ehrrg", "u": "hrmhm", "v": "hrrrm", "w": "hwurgh",
                             "x": "murr", "y": "hurr", "z": "mhehmem"}

        # Allowed characters for command prefixes
        self.allowedChars = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                             "~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "+", "=", "[", "]", "{", "}", ";", ":", "|", "/", ".", "?", ">", "<", ",",)

        with open("data/playing_list.json", "r") as playing_list:
            self.playingList = json.load(playing_list)

        with open("data/cursed_images.json", "r") as cursed_images:
            self.cursedImages = json.load(cursed_images)

        with open("data/minecraft_servers.json", "r") as mc_servers:
            self.mcServers = json.load(mc_servers)

        with open("data/items.json", "r") as items:
            self.items = json.load(items)

        with open("data/shop_items.json", "r") as shop_items:
            self.shop_items = json.load(shop_items)


def setup(bot):
    bot.add_cog(Global(bot))
