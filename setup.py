import os
from os.path import join, dirname

from setuptools import setup, find_packages

os.umask(0o022)

setup(
    name='legi',
    version='0.0',
    description="Tools to work with the database of French laws (LEGI)",
    author='Changaco',
    author_email='changaco@changaco.oy.lc',
    url='https://github.com/Legilibre/legi.py',
    license='CC0',
    packages=find_packages(exclude=['tests']),
    long_description="See https://github.com/Legilibre/legi.py",
    install_requires=open(join(dirname(__file__), 'requirements.txt')).read(),
    keywords='legi law france',
)
