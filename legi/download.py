"""
Downloads the LEGI tarballs from the official FTP server.
"""

import argparse
import ftplib
import os
import sys
from time import sleep
import traceback
import urllib.parse

import lxml.html
import requests


DILA_FTP_HOST = 'echanges.dila.gouv.fr'
DILA_FTP_PORT = 21
DILA_HTTP_URL = 'https://echanges.dila.gouv.fr/OPENDATA'
DILA_LEGI_DIR = '/LEGI'


def log(*args, **kw):
    kw.setdefault('file', sys.stderr)
    print(*args, **kw)


def download_legi(dst_dir, retry_hours=0):
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)
    sleep_hours = 0
    while True:
        try:
            try:
                download_legi_via_ftp(dst_dir)
            except Exception:
                download_legi_via_http(dst_dir)
            break
        except Exception:
            # Retry in an hour, unless we've reached our time limit
            sleep_hours += 1
            if sleep_hours > retry_hours:
                raise
            traceback.print_exc()
        log("Waiting an hour before retrying...")
        try:
            sleep(3600)
        except KeyboardInterrupt:
            sys.exit(1)


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
    log('{} remote files, {} common files, {} missing files'.format(
        len(remote_files), len(common_files), len(missing_files),
    ))
    for filename in missing_files:
        filepath = os.path.join(dst_dir, filename)
        with open(filepath + '.part', mode='a+b') as fh:
            offset = fh.tell()
            if offset:
                log('Continuing the download of the file ' + filename)
            else:
                log('Downloading the file ' + filename)
            ftph.retrbinary('RETR ' + filename, fh.write, rest=offset)
        os.rename(filepath + '.part', filepath)
    ftph.quit()


def download_legi_via_http(dst_dir):
    local_files = set(os.listdir(dst_dir))
    log("Downloading the index page...")
    sess = requests.Session()
    base_url = DILA_HTTP_URL + DILA_LEGI_DIR + '/'
    r = sess.get(base_url)
    assert r.status_code == 200, r
    remote_files, common_files, missing_files = set(), [], []
    html = lxml.html.document_fromstring(r.text)
    for url in html.xpath('//a/@href'):
        url = urllib.parse.urljoin(base_url, url)
        if not url.startswith(base_url):
            continue
        url = urllib.parse.urlsplit(url)
        filename = url.path.rsplit('/', 1)[-1]
        if '.tar.' not in filename:
            continue
        if filename in remote_files:
            continue
        remote_files.add(filename)
        if filename in local_files:
            common_files.append(filename)
        else:
            missing_files.append(filename)
    log('{} remote files, {} common files, {} missing files'.format(
        len(remote_files), len(common_files), len(missing_files),
    ))
    for filename in missing_files:
        filepath = os.path.join(dst_dir, filename)
        url = base_url + filename
        with open(filepath + '.part', mode='a+b') as fh:
            offset = fh.tell()
            if offset:
                log('Continuing the download of the file ' + filename)
                headers = {'Range': f'bytes={offset}-'}
            else:
                log('Downloading the file ' + filename)
                headers = None
            r = sess.get(url, headers=headers, stream=True)
            if offset:
                if r.status_code == 200:
                    # It looks like the server is sending the whole file instead
                    # of only the requested range.
                    fh.seek(0)
                elif r.status_code == 416:
                    # It looks like we had already finished downloading this file.
                    os.rename(filepath + '.part', filepath)
                    continue
                else:
                    assert r.status_code == 206, r
            else:
                assert r.status_code == 200, r
            for chunk in r.iter_content(chunk_size=None):
                fh.write(chunk)
        os.rename(filepath + '.part', filepath)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    p.add_argument('-r', '--retry', action='store_true', default=False,
                   help="if the download fails, retry every hour for up to 6 hours")
    args = p.parse_args()
    retry_hours = 6 if args.retry else 0
    download_legi(args.directory, retry_hours=retry_hours)
