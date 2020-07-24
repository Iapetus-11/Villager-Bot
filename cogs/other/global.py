import arrow
import discord
import json
from discord.ext import commands


class Global(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Stats command stuffs
        self.msg_count = 0
        self.cmd_count = 0
        self.vote_count = 0

        self.startTime = arrow.utcnow()

        self.enchantLang = {"a": "ᔑ", "b": "ʖ", "c": "ᓵ", "d": "↸", "e": "ᒷ",
                            "f": "⎓", "g": "⊣", "h": "⍑", "i": "╎", "j": "⋮",
                            "k": "ꖌ", "l": "ꖎ", "m": "ᒲ", "n": "リ", "o": "𝙹", "p": "!¡",
                            "q": "ᑑ", "r": "∷", "s": "ᓭ", "t": "ℸ ̣", "u": "⚍",
                            "v": "⍊", "w": "∴", "x": "̇/", "y": "‖", "z": "⨅"}

        self.villagerLang = {"a": "hruh", "b": "hur", "c": "hurgh", "d": "hdur", "e": "mreh", "f": "hrgh",
                             "g": "hg", "h": "hhh", "i": "ehr", "j": "hrg", "k": "hregh", "l": "hrmg",
                             "m": "hrmm", "n": "hmeh", "o": "hugh", "p": "hrum", "q": "huerhg", "r": "hrrrh",
                             "s": "surgghm", "t": "ehrrg", "u": "hrmhm", "v": "hrrrm", "w": "hwurgh",
                             "x": "murr", "y": "hurr", "z": "mhehmem"}

        # Allowed characters for command prefixes
        self.allowedChars = (
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
        "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "+", "=", "[", "]", "{", "}", ";", ":", "|",
        "/", ".", "?", ">", "<", ",",)

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

        self.command_leaderboard = {}

        self.honey_buckets = None

        self.triggering_cmds = ["mine", "withdraw", "deposit", "shop", "give_stuff", "sell_item", "give_item", "gamble",
                                "pillage", "use_potion", "harvest_honey"]

        self.spawn_chance = 25

        self.pause_econ = []  # uid... uid

        self.pillage_limit = {}

        self.track_votes = True


def setup(bot):
    bot.add_cog(Global(bot))
