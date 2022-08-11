import numpy
import pyximport

def build_tiler():
    # add cython support, with numpy header files
    pyximport.install(language_level=3, setup_args={"include_dirs": numpy.get_include()})

    import bot.utils.tiler  # noqa: F401
