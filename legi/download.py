"""
Downloads the LEGI tarballs from the official FTP server.
"""

import argparse
import ftplib
import os
from time import sleep
import traceback


DILA_FTP_HOST = 'echanges.dila.gouv.fr'
DILA_FTP_PORT = 21
DILA_LEGI_DIR = '/LEGI'


def download_legi(dst_dir, retry_hours=0):
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)
    sleep_hours = 0
    while True:
        try:
            download_legi_via_ftp(dst_dir)
            break
        except Exception:
            # Retry in an hour, unless we've reached our time limit
            sleep_hours += 1
            if sleep_hours > retry_hours:
                raise
            traceback.print_exc()
            print("Waiting an hour before retrying...")
            sleep(3600)


def download_legi_via_ftp(dst_dir):
    local_files = set(os.listdir(dst_dir))
    ftph = ftplib.FTP()
    ftph.connect(DILA_FTP_HOST, DILA_FTP_PORT)
    ftph.login()
    ftph.cwd(DILA_LEGI_DIR)
    remote_files = [filename for filename in ftph.nlst() if '.tar.' in filename]
    common_files = [f for f in remote_files if f in local_files]
    missing_files = [f for f in remote_files if f not in local_files]
    ftph.voidcmd('TYPE I')
    print('{} remote files, {} common files, {} missing files'.format(
        len(remote_files), len(common_files), len(missing_files),
    ))
    for filename in missing_files:
        filepath = os.path.join(dst_dir, filename)
        with open(filepath + '.part', mode='a+b') as fh:
            offset = fh.tell()
            if offset:
                print('Continuing the download of the file ' + filename)
            else:
                print('Downloading the file ' + filename)
            ftph.retrbinary('RETR ' + filename, fh.write, rest=offset)
        os.rename(filepath + '.part', filepath)
    ftph.quit()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    p.add_argument('-r', '--retry', action='store_true', default=False,
                   help="if the download fails, retry every hour for up to 6 hours")
    args = p.parse_args()
    retry_hours = 6 if args.retry else 0
    download_legi(args.directory, retry_hours=retry_hours)
