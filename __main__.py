import pyximport

pyximport.install(language_level=3, reload_support=True)

import src.bot as bot

if __name__ == "__main__":
    bot.main()
