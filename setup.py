from Cython.Build import cythonize
from setuptools import setup

setup(
    name="Villager Bot",
    ext_modules=cythonize([]),
    zip_safe=False
)
