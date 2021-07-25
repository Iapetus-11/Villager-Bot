import numpy
import sys
import os

try:  # add optional cython support
    import pyximport
except ImportError as e:
    print(e)
    pyximport = None

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

if pyximport:
    # add cython support, with numpy header files
    pyximport.install(language_level=3, setup_args={"include_dirs": numpy.get_include()})

    # import and compile villager bot cython modules here **first**
    # if not all pyx files are imported here, each forked process / shard group will try to compile
    # them and fail because they are all trying at the same time to access and write the same files
    from util import tiler, tiler_rgba

from karen import MechaKaren


def main():
    karen = MechaKaren()

    try:
        karen.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
