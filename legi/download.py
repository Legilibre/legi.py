"""
Downloads the LEGI tarballs from the official FTP server. Uses `wget` for now.
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from subprocess import check_call


def download_legi(tar_dir):
    check_call([
        'wget', '-c', '-N', '--no-remove-listing', '-nH', '-P', tar_dir,
        'ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/*legi_*'
    ])


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('directory')
    args = p.parse_args()
    download_legi(args.directory)
