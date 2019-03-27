import os
from os.path import join, dirname

from setuptools import setup, find_packages

from version import get_version

os.umask(0o022)

setup(
    name='dila2sql',
    version=get_version(),
    description="SQL importer for French legal OpenData and cleaning tools",
    author='SocialGouv',
    author_email='contact@num.social.gouv.fr',
    url='https://github.com/SocialGouv/dila2sql',
    license='CC0',
    packages=find_packages(exclude=['tests']),
    long_description="See https://github.com/SocialGouv/dila2sql",
    install_requires=open(join(dirname(__file__), 'requirements.txt')).read(),
    keywords='dila law france legi kali jorf postgresql opendata',
    include_package_data=True,
    zip_safe=False,
)
