from setuptools import setup, find_packages
from tuls import __version__

setup(
    name='tuls',
    version=__version__,
    packages=find_packages(),
    install_requires=['cryptography']
)
