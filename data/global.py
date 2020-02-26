from discord.ext import commands
import discord
import arrow

class Global(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.startTime = arrow.utcnow()
        
        self.enchantLang = {"a": "\u1511", "b": "\u0296", "c": "\u14f5", "d": "\u21b8", "e": "\u14b7",
                            "f": "\u2393", "g": "\u22a3", "h": "\u2351", "i": "\u254e", "Ｊ": "\u22ee",
                            "k": "\ua58c", "l": "\ua58e", "m": "\u14b2", "n": "\u30ea", "o": "o", "p": "!\u00a1",
                            "q": "\u1451", "r": "\u2237", "s": "\u14ed", "t": "\u2138", "u": "\u268d",
                            "v": "\u234a", "w": "\u2234", "x": "\u0307", "y": "‖", "z": "\u2a05"}
        
        self.villagerLang = {"a": "hruh", "b": "hur", "c": "hurgh", "d": "hdur", "e": "mreh", "f": "hrgh",
                            "g": "hg", "h": "hhh", "i": "ehr", "j": "hrg", "k": "hregh", "l": "hrmg",
                            "m": "hrmm", "n": "hmeh", "o": "hugh", "p": "hrum", "q": "huerhg", "r": "hrrrh",
                            "s": "surgghm", "t": "ehrrg", "u": "hrmhm", "v": "hrrrm", "w": "hwurgh",
                            "x": "murr", "y": "hurr", "z": "mhehmem"}
        
        self.playingList = ["Minecraft", "!!vote for emeralds!", "Minecraft Java Edition", "Minecraft with PewDiePie",
                            "Minecraft with CaptainSparklez", "Minecraft with JackSepticEye", "Minecraft Bedrock Edition",
                            "Minecraft on Xenon Gaming", "Minecraft on Hypixel", "Minecraft on a TI-84",
                            "Minecraft on a Commodore 64", "!!vote for emeralds!", "Minecraft on a Raspberry Pi",
                            "Minecraft online", "Minecraft with Iapetus11", "Minecraft with Iapetus11",
                            "Minecraft Raspberry Pi Edition", "Minecraft Pocket Edition Lite",
                            "Minecraft with stampylonghead", "Minecraft with PopularMMOs", "Minecraft with DanTDM",
                            "Minecraft with Bajan Canadian", "Minecraft with the comrades", "Minecraft Xbox One Edition",
                            "Minecraft PS4 Edition", "Minecraft Console Edition", "Minecraft Pocket Edition",
                            "Minecraft on Windows XP", "Minecraft on Windows 98", "!!vote for emeralds!",
                            "Minecraft on MS-DOS", "Minecraft on a typewriter", "Minecraft on a TV remote", "Minecraft 1.0",
                            "Minecraft 1.12.2", "Minecraft 1.14.4", "Minecraft on a Nintendo Switch",
                            "Minecraft 1.14.4 on MSDOS", "Minecraft at school", "Minecraft in Minecraft",
                            "Minecraft in a chest in Minecraft", "Minecraft VR", "Minecraft with Ray Tracing",
                            "Minecraft with Ultra-HD Shaders", "Minecraft with Ultra-HD Textures", "CraftMine 4.41.1",
                            "Minecraft with BEES", "Minecraft on the Xenon Gaming servers", "Minecraft Classic",
                            "Minecraft Classic Online", "Minecraft on a microwave", "Minecraft with PewDiePack",
                            "Minecraft with Iapetus11 on Xenon BE", "Minecraft Earth", "Minecraft Earth Beta",
                            "Minecraft Dungeons", "on Hypixel", "Skyblock", "Spleef", "!!vote for emeralds!", "Factions",
                            "PVP on Hypixel", "Hypixel Pit", "CraftMine 1.0", "Майнкрафт", "46 75 63 6b 69 6e 67 20 4e 65 72 64",
                            "4d 69 6e 65 63 72 61 66 74",
                            "01001101 01101001 01101110 01100101 01100011 01110010 01100001 01100110 01110100",
                            "FortCraft Mine Royale", "with creepers", "!!vote for emeralds!", "Minecraft with Joe!",
                            "Minecraft 1.15.1", "Minecraft with a lot of beeeeeeeeeeees", "Minecraft on Xenon JE",
                            "Minecraft on Xenon BE", "Minecraft with Iapetus11", "Minecraft with Iapetus11",
                            "with all the baby villagers in the village", "jack up the prices in the Villager Shop"]
        
        self.cursedImages = ["airr.png", "alexaandstevena.jpg", "animals.png", "armedanddangerouscreeper.png",
                            "asmallgraphicalerror.png", "barrelchest.jpg", "beans.jpg", "beewither.jpg", "bootsword.png",
                            "brokenvillagers.jpg", "buffsteve.png", "buffsteve2.png", "burntchickennugget.jpg",
                            "censored1.jpg", "chaftingfurnset.png", "chair.png", "chest1.png", "chester.jpg",
                            "chestman.jpg", "chestnugget.jpg", "circularcreeper.png", "circularportal.jpg",
                            "coalaxe.jpg", "cow.jpg", "creeperbees.jpg", "creeperwithfeet.png", "creepigandpigger.jpg",
                            "crispysteve.jpg", "cursedredstone.jpg", "cursedstairs.png", "cursedsteves.jpg",
                            "diagonalgrass.png", "diagonalpiston.jpg", "diagonalportal.jpg", "diamondcrafting.png",
                            "diamondcreeper.jpg", "diamondnugget.jpg", "diamondpickaxe.png", "dirtmonds.jpg",
                            "doubelfurnace.jpg", "doubleenderchest.jpg", "doublerailchest.jpg",
                            "enchantingtablebutnobooks.png", "enderchestportal.jpg", "endermaninwater.jpg",
                            "entherportal.jpg", "expensivedirthouse.png", "expensivegrass.png", "f.png",
                            "firebutonwater.png", "flipphoneminecraft.jpg", "gamergirlbathwater.jpg",
                            "gianthulkzombiesteve.png", "giantmutantcreeper.png", "gtacraft.jpg",
                            "halfslabofdirt.png", "heqq.png", "illegalshape.jpg", "inveretedportal.png",
                            "invertedfencesandwalls.png", "inverted_furnace.jpg", "ironwoodenpick.jpg",
                            "lavawaterslabs.png", "longboichest.jpg", "longfurnace.jpg", "longhoe.jpg", "longpiston.jpg",
                            "manypickaxe.jpg", "minedlava.jpg", "mineladder.jpg", "minepig.jpg", "morecursedstairs.jpg",
                            "multiboss.png", "multipiston.png", "multishotfishingrod.png", "nethershortal.png",
                            "oakwoodingot.jpg", "pandas.jpg", "perfectlybalancedasallthingsshouldbe.png",
                            "pickaxewooden.png", "pignig.jpg", "pistonnotsip.png", "porkchopwood.jpg",
                            "rainingtorches.jpg", "realisticlivestock.jpg", "redstone.jpg", "redstonewither.png",
                            "ricardogolem.png", "rippedsteve.png", "roundmc.png", "roundsteve.png", "sandcoalore.png",
                            "scaredvillager.png", "sexysteve.jpg", "sidewaysbed.jpg", "sidewayschest.jpg",
                            "sidewayschest2.jpg", "slabs.png", "smallboichest.jpg", "spidercreep.jpg", "spooktober.jpg",
                            "stairchest.jpg", "stevebutapig.jpg", "stevedragon.png", "stevesteve.png", "stevetposing.jpg",
                            "stevewithfingers.png", "stevewithfingers2.jpg", "stoneore.png", "suicidalsteve.jpg",
                            "svillager.png", "tallchest.jpg", "tallvillager.png", "teslacraft.jpg", "thiccboichest.jpg",
                            "thiccsteve2.png", "thing.py", "triangularcraftingtable.jpg", "underwaterenderman.png",
                            "verticalminecart.jpg", "verticalredstone.png", "villader.png", "villagerghast.jpg",
                            "villagerup.png", "watermelooon.png", "wava.png", "winniethepooandtrump.jpg", "xwingcraft.jpg",
                            "angrychest.jpg", "brazzers.JPG", "cacti.jpg", "chestdir.jpg", "chonker.jpg", "chonker2.png",
                            "emeraldingot.jpg", "fatherobrine.gif", "gardens.jpg", "halftnt.jpg", "longpiston3.jpg",
                            "piggo.jpg", "pool.jpg", "squiddyvillager.jpg", "stevebutacow.jpg", "stevehd.jpg", "tinysteve.jpg",
                            "4dimensionalbed.png", "angrydoggo.jpg", "beaconballs.png", "pistonblock22.png", "roundlog.png",
                            "shep420.gif", "pillagerbarrel.png"]
        
def setup(bot):
    bot.add_cog(Global(bot))