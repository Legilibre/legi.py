
"""
Imports DILA tar archives into SQL databases
"""

from argparse import ArgumentParser
from fnmatch import fnmatch
import os
import re

from .process_archive import process_archive
from dila2sql.anomalies import detect_anomalies
from dila2sql.utils import connect_db, partition
from dila2sql.models import db_proxy, DBMeta, TexteVersionBrute, Lien


def main():
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('--directory', default="/var/lib/dila2sql/original_dumps")
    p.add_argument('--anomalies', action='store_true', default=False,
                   help="detect anomalies after each processed archive")
    p.add_argument('--anomalies-dir', default='.')
    p.add_argument('--pragma', action='append', default=[],
                   help="Doc: https://www.sqlite.org/pragma.html | Example: journal_mode=WAL")
    p.add_argument('--raw', default=False, action='store_true')
    p.add_argument('--base', choices=["LEGI", "JORF", "KALI"])
    p.add_argument('--skip-links', default=False, action='store_true',
                   help="if set, all link metadata will be ignored (the `liens` table will be empty)")
    args = p.parse_args()

    if not os.path.isdir(args.anomalies_dir):
        os.mkdir(args.anomalies_dir)

    db_url = args.db
    db = connect_db(db_url)
    db_proxy.initialize(db)

    db_meta_base = DBMeta.get_or_none(key='base')
    base = db_meta_base.value if db_meta_base else None
    db_meta_last_update = DBMeta.get_or_none(key='last_update')
    last_update = db_meta_last_update.value if db_meta_last_update else None

    if not base:
        base = args.base.upper() if args.base and not last_update else 'LEGI'
        DBMeta.create(key='base', value=base)
    if args.base and base != args.base.upper():
        print('!> Wrong database: requested '+args.base.upper()+' but existing database is '+base+'.')
        raise SystemExit(1)

    if base != 'LEGI' and not args.raw:
        print("!> You need to use the --raw option when working with bases other than LEGI.")
        raise SystemExit(1)

    if base != 'LEGI' and args.anomalies:
        print("!> The --anomalies option can only be used with the LEGI base")
        raise SystemExit(1)

    # Check and record the data mode
    db_meta_raw = DBMeta.get_or_none(key='raw')
    db_meta_raw = db_meta_raw.value if db_meta_raw else None
    if args.raw:
        versions_brutes = bool(TexteVersionBrute.get_or_none())
        data_is_not_raw = versions_brutes or db_meta_raw is False
        if data_is_not_raw:
            print("!> Can't honor --raw option, the data has already been modified previously.")
            raise SystemExit(1)
    if db_meta_raw != args.raw:
        DBMeta.insert(key='raw', value=args.raw) \
            .on_conflict(conflict_target=[DBMeta.key], preserve=[DBMeta.value]) \
            .execute()

    # Handle the --skip-links option
    has_links = bool(Lien.get_or_none())
    if not args.skip_links and not has_links and last_update is not None:
        args.skip_links = True
        print("> Warning: links will not be processed because this DB was built with --skip-links.")
    elif args.skip_links and has_links:
        print("> Deleting links...")
        Lien.delete()

    # Look for new archives in the given directory
    print("> last_update is", last_update)
    archive_re = re.compile(r'(.+_)?'+base.lower()+r'(?P<global>_global|_)?_(?P<date>[0-9]{8}-[0-9]{6})\..+', flags=re.IGNORECASE)
    skipped = 0
    archives = sorted([
        (m.group('date'), bool(m.group('global')), m.group(0)) for m in [
            archive_re.match(fn) for fn in os.listdir(args.directory)
            if fnmatch(fn.lower(), '*'+base.lower()+'_*.tar.*')
        ]
    ])
    most_recent_global = [t[0] for t in archives if t[1]][-1]
    if last_update and most_recent_global > last_update:
        print("> There is a new global archive, recreating the DB from scratch!")
        raise Exception("not implemented yet")
        # db.close()
        # os.rename(db.address, db.address + '.back')
        # db = connect_db(args.db, pragmas=args.pragma)
    archives, skipped = partition(
        archives, lambda t: t[0] >= most_recent_global and t[0] > (last_update or '')
    )
    if skipped:
        print("> Skipped %i old archives" % len(skipped))

    # Process the new archives
    for archive_date, is_global, archive_name in archives:
        print("> Processing %s..." % archive_name)
        process_archive(db, db_url, args.directory + '/' + archive_name, not args.skip_links)
        DBMeta.insert(key='last_update', value=archive_date) \
            .on_conflict(conflict_target=[DBMeta.key], preserve=[DBMeta.value]) \
            .execute()
        last_update = archive_date
        print('last_update is now set to', last_update)

        # Detect anomalies if requested
        if args.anomalies:
            fpath = args.anomalies_dir + '/anomalies-' + last_update + '.txt'
            with open(fpath, 'w') as f:
                n_anomalies = detect_anomalies(db, f)
            print("logged", n_anomalies, "anomalies in", fpath)

    if not args.raw:
        from .normalize import normalize_text_titles
        normalize_text_titles(db)
        from .factorize import main as factorize
        factorize(db)
        from .normalize import normalize_article_numbers
        normalize_article_numbers(db)


if __name__ == '__main__':
    main()
