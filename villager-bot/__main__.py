import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # ensure villager bot modules are accessible
os.chdir(os.path.dirname(__file__))  # ensure the current working directory is correct

from karen import MechaKaren


if __name__ == "__main__":
    karen = MechaKaren()

    try:
        karen.run()
    except KeyboardInterrupt:
        pass
