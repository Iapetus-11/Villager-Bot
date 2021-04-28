import pyximport
import numpy

pyximport.install(language_level=3, reload_support=True, setup_args={"include_dirs": numpy.get_include()})

import src.bot as bot

if __name__ == "__main__":
    bot.run()
