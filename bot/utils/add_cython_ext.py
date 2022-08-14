import logging
import numpy


def add_cython_ext():
    try:
        import pyximport

        # add cython support, with numpy header files
        pyximport.install(language_level=3, setup_args={"include_dirs": numpy.get_include()})

        import bot.utils.tiler  # noqa: F401
    except Exception:
        logging.error("An error occurred while setting up Cython extensions", exc_info=True)
