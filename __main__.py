import pyximport

pyximport.install(language_level=3)

import src.bot as bot

if __name__ == "__main__":
    bot.main()
