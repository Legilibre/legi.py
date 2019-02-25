"""
Downloads the LEGI tarballs from the official FTP server.
"""

import argparse
import os
from urllib.request import urlopen
import lxml.html
import re
import asyncio
import aiohttp
import aiofiles
import backoff


DILA_URL = "https://echanges.dila.gouv.fr/OPENDATA"

HANDLED_EXCEPTIONS = (
    aiohttp.ClientError,
    aiohttp.client_exceptions.ServerDisconnectedError,
    aiohttp.client_exceptions.ClientPayloadError
)


@backoff.on_exception(backoff.expo, HANDLED_EXCEPTIONS, max_time=5)
async def fetch_size(base, filename, session):
    url = "%s/%s/%s" % (DILA_URL, base, filename)
    async with session.head(url) as response:
        return (filename, response.headers['Content-Length'])


async def fetch_sizes(base, filenames):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=20)) as session:
        tasks = [asyncio.ensure_future(fetch_size(base, f, session)) for f in filenames]
        return await asyncio.gather(*tasks)


def filter_link(filename, base):
    return bool(re.match(r"%s_[0-9\-]+\.tar\.gz" % base, filename)) \
        or bool(re.match(r"Freemium_%s_(global)?_[0-9\-]+\.tar\.gz" % base.lower(), filename))


@backoff.on_exception(backoff.expo, HANDLED_EXCEPTIONS, max_time=20)
async def download_file(base, filename, dst_dir, session):
    filepath = os.path.join(dst_dir, filename)
    url = "%s/%s/%s" % (DILA_URL, base, filename)
    async with session.get(url) as resp:
        if resp.status == 200:
            f = await aiofiles.open(filepath, mode='wb')
            await f.write(await resp.read())
            await f.close()


@backoff.on_exception(backoff.expo, HANDLED_EXCEPTIONS, max_time=20)
async def download_files(base, filenames, dst_dir):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=10)) as session:
        tasks = [
            asyncio.ensure_future(download_file(base, f, dst_dir, session))
            for f in filenames
        ]
        return await asyncio.gather(*tasks)


def download_legi(dst_dir, base='LEGI'):
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)
    local_files = {filename: {} for filename in os.listdir(dst_dir)}

    print("Reading index page for base %s ..." % base)
    url = "%s/%s" % (DILA_URL, base)
    f = urlopen(url)
    raw_html = f.read().decode('utf-8')
    lxml_doc = lxml.html.document_fromstring(raw_html)
    links = [l[2] for l in lxml_doc.iterlinks()]
    remote_files = [os.path.basename(l.split("/")[-1]) for l in links]
    remote_files = [l for l in remote_files if filter_link(l, base)]
    common_files = [f for f in remote_files if f in local_files]
    missing_files = [f for f in remote_files if f not in local_files]
    remote_files = {filename: {} for filename in remote_files}
    for filename in common_files:
        local_files[filename]['size'] = os.path.getsize(
            os.path.join(dst_dir, filename)
        )

    print("fetching size of %s remote files ..." % len(common_files))
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_sizes(base, common_files))
    common_file_sizes = loop.run_until_complete(future)
    for common_file_size in common_file_sizes:
        remote_files[common_file_size[0]]['size'] = int(common_file_size[1])

    invalid_files = []
    for filename in common_files:
        if ('size' in remote_files[filename] and local_files[filename]['size'] != remote_files[filename]['size']):
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
        print('Removing file {} because it has a different size'.format(filename))
        os.remove(os.path.join(dst_dir, filename))

    files_to_download = invalid_files + missing_files
    print("Starting to download %s files ..." % len(files_to_download))
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(download_files(base, files_to_download, dst_dir))
    loop.run_until_complete(future)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    p.add_argument('--base', default='LEGI')
    args = p.parse_args()
    if args.base not in ["LEGI", "JORF", "KALI"]:
        print('!> Non-existing database "'+args.base+'".')
        raise SystemExit(1)
    download_legi(args.directory, args.base)
