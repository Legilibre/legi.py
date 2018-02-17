"""
Downloads the LEGI tarballs from the official FTP server.
"""

from __future__ import division, print_function, unicode_literals

import argparse
import ftplib
import os


DILA_FTP_HOST = 'echanges.dila.gouv.fr'
DILA_FTP_PORT = 21
DILA_LEGI_DIR = '/LEGI'


def download_legi(dst_dir):
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)
    local_files = {filename: {} for filename in os.listdir(dst_dir)}
    ftph = ftplib.FTP()
    ftph.connect(DILA_FTP_HOST, DILA_FTP_PORT)
    ftph.login()
    ftph.cwd(DILA_LEGI_DIR)
    remote_files = [filename for filename in ftph.nlst() if 'legi_' in filename]
    common_files = [f for f in remote_files if f in local_files]
    missing_files = [f for f in remote_files if f not in local_files]
    remote_files = {filename: {} for filename in remote_files}
    for filename in common_files:
        local_files[filename]['size'] = os.path.getsize(
            os.path.join(dst_dir, filename)
        )
    ftph.voidcmd('TYPE I')
    for filename in remote_files:
        file_size = ftph.size(filename)
        remote_files[filename]['size'] = int(file_size)
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
    for filename in missing_files:
        filepath = os.path.join(dst_dir, filename)
        with open(filepath, mode='wb') as fh:
            print('Downloading the file {}'.format(filename))
            ftph.retrbinary('RETR {}'.format(filename), fh.write, rest=0)
    ftph.quit()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    args = p.parse_args()
    download_legi(args.directory)
