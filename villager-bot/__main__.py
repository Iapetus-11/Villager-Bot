import pyximport
import numpy
import sys
import os

# add cython support, with numpy header files
pyximport.install(language_level=3, reload_support=True, setup_args={"include_dirs": numpy.get_include()})

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from karen import MechaKaren


if __name__ == "__main__":
    karen = MechaKaren()

    try:
        karen.run()
    except KeyboardInterrupt:
        pass
