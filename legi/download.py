"""
Downloads the LEGI tarballs from the official FTP server.
"""

from __future__ import division, print_function, unicode_literals

import argparse
import datetime
import ftplib
import os
import time


DILA_FTP_HOST = 'echanges.dila.gouv.fr'
DILA_FTP_PORT = 21
DILA_LEGI_DIR = '/LEGI'


EPOCH_DATETIME = datetime.datetime.fromtimestamp(0)


def to_epoch_time(date):
    return (date - EPOCH_DATETIME).total_seconds()


def download_legi(dst_dir):
    local_files = {filename: {} for filename in os.listdir(dst_dir)}
    ftph = ftplib.FTP()
    ftph.connect(DILA_FTP_HOST, DILA_FTP_PORT)
    ftph.login()
    ftph.cwd(DILA_LEGI_DIR)
    remote_files = {filename: {} for filename in ftph.nlst() if 'legi_' in filename}
    local_set = set(local_files.keys())
    remote_set = set(remote_files.keys())
    common_files = list(local_set & remote_set)
    missing_files = list(remote_set - local_set)
    for filename in common_files:
        local_files[filename]['size'] = os.path.getsize(
            os.path.join(dst_dir, filename)
        )
    ftph.voidcmd('TYPE I')
    for filename in remote_files:
        tmp = ftph.sendcmd('MDTM {}'.format(filename)).split(' ', 1)[1]
        file_mtim = datetime.datetime.strptime(tmp, '%Y%m%d%H%M%S')
        file_size = ftph.size(filename)
        remote_files[filename]['size'] = int(file_size)
        remote_files[filename]['mtim'] = file_mtim
    invalid_files = []
    for filename in common_files:
        if local_files[filename]['size'] < remote_files[filename]['size']:
            invalid_files.append(filename)
    print(
        '{} remote files, {} common files ({} invalid), {} missing files'
        .format(
            len(remote_files),
            len(common_files), len(invalid_files),
            len(missing_files)
        )
    )
    for filename in invalid_files:
        filepath = os.path.join(dst_dir, filename)
        with open(filepath, mode='a+b') as fh:
            print('Continuing the download of the file {}'.format(filename))
            ftph.retrbinary(
                'RETR {}'.format(filename),
                fh.write,
                rest=local_files[filename]['size']
            )
        # Pas facile de récupérer un timestamp en Python 2...
        os.utime(
            filepath, (
                time.time(), to_epoch_time(remote_files[filename]['mtim'])
            )
        )
    for filename in missing_files:
        filepath = os.path.join(dst_dir, filename)
        with open(filepath, mode='wb') as fh:
            print('Downloading the file {}'.format(filename))
            ftph.retrbinary('RETR {}'.format(filename), fh.write, rest=0)
        os.utime(
            filepath, (
                time.time(), to_epoch_time(remote_files[filename]['mtim'])
            )
        )
    ftph.quit()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    args = p.parse_args()
    download_legi(args.directory)
