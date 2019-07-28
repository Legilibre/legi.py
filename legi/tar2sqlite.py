"""
Extracts LEGI tar archives into an SQLite DB
"""

from argparse import ArgumentParser
from fnmatch import fnmatch
import json
import os
import re

import libarchive
from lxml import etree

try:
    from tqdm import tqdm
except ImportError:
    print('[warning] tqdm is not installed, the progress bar is disabled')
    tqdm = lambda x: x

from .anomalies import detect_anomalies
from .utils import connect_db, partition


SOUS_DOSSIER_MAP = {
    'articles': 'article',
    'sections': 'section_ta',
    'textes_structs': 'texte/struct',
    'textes_versions': 'texte/version',
}


def count(d, k, c):
    if c == 0:
        return
    try:
        d[k] += c
    except KeyError:
        d[k] = c


def innerHTML(e):
    r = etree.tostring(e, encoding='unicode', with_tail=False)
    return r[r.find('>')+1:-len(e.tag)-3]


def scrape_tags(attrs, root, wanted_tags, unwrap=False):
    attrs.update(
        (e.tag.lower(), (innerHTML(e[0]) if unwrap else innerHTML(e)) or None)
        for e in root if e.tag in wanted_tags
    )


def suppress(get_table, db, liste_suppression):
    counts = {}
    for path in liste_suppression:
        parts = path.split('/')
        assert parts[0] == 'legi'
        text_cid = parts[11]
        text_id = parts[-1]
        assert len(text_id) == 20
        table = get_table(parts)
        sous_dossier = SOUS_DOSSIER_MAP[table]
        db.run("""
            DELETE FROM {0}
             WHERE dossier = ?
               AND cid = ?
               AND id = ?
        """.format(table), (parts[3], text_cid, text_id))
        changes = db.changes()
        if changes:
            count(counts, 'delete from ' + table, changes)
            # Also delete derivative data
            if table in ('articles', 'textes_versions'):
                db.run("""
                    DELETE FROM liens
                     WHERE src_id = ? AND NOT _reversed
                        OR dst_id = ? AND _reversed
                """, (text_id, text_id))
                count(counts, 'delete from liens', db.changes())
            elif table == 'sections':
                db.run("""
                    DELETE FROM sommaires
                     WHERE cid = ?
                       AND parent = ?
                       AND _source = 'section_ta_liens'
                """, (text_cid, text_id))
                count(counts, 'delete from sommaires', db.changes())
            elif table == 'textes_structs':
                db.run("""
                    DELETE FROM sommaires
                     WHERE cid = ?
                       AND _source = 'struct/' || ?
                """, (text_cid, text_id))
                count(counts, 'delete from sommaires', db.changes())
            # And delete the associated row in textes_versions_brutes if it exists
            if table == 'textes_versions':
                db.run("DELETE FROM textes_versions_brutes WHERE id = ?", (text_id,))
                count(counts, 'delete from textes_versions_brutes', db.changes())
            # If the file had an older duplicate that hasn't been deleted then
            # we have to fall back to that, otherwise we'd be missing data
            older_file = db.one("""
                SELECT *
                  FROM duplicate_files
                 WHERE id = ?
                   AND sous_dossier = ?
              ORDER BY mtime DESC
                 LIMIT 1
            """, (text_id, sous_dossier), to_dict=True)
            if older_file:
                db.run("""
                    DELETE FROM duplicate_files
                     WHERE dossier = ?
                       AND cid = ?
                       AND sous_dossier = ?
                       AND id = ?
                """, (older_file['dossier'], older_file['cid'], sous_dossier, older_file['id']))
                count(counts, 'delete from duplicate_files', db.changes())
                for table, rows in json.loads(older_file['data']).items():
                    if isinstance(rows, dict):
                        rows['id'] = older_file['id']
                        rows['cid'] = older_file['cid']
                        rows['dossier'] = older_file['dossier']
                        rows['mtime'] = older_file['mtime']
                        rows = (rows,)
                    for row in rows:
                        db.insert(table, row)
                    count(counts, 'insert into ' + table, len(rows))
        else:
            # Remove the file from the duplicates table if it was in there
            db.run("""
                DELETE FROM duplicate_files
                 WHERE dossier = ?
                   AND cid = ?
                   AND sous_dossier = ?
                   AND id = ?
            """, (parts[3], text_cid, sous_dossier, text_id))
            count(counts, 'delete from duplicate_files', db.changes())
    total = sum(counts.values())
    print("made", total, "changes in the database based on liste_suppression_legi.dat:",
          json.dumps(counts, indent=4, sort_keys=True))


def process_archive(db, archive_path, process_links=True):

    # Define some constants
    ARTICLE_TAGS = set('NOTA BLOC_TEXTUEL'.split())
    SECTION_TA_TAGS = set('TITRE_TA COMMENTAIRE'.split())
    TEXTELR_TAGS = set('VERSIONS'.split())
    TEXTE_VERSION_TAGS = set('VISAS SIGNATAIRES TP NOTA ABRO RECT'.split())
    META_ARTICLE_TAGS = set('NUM ETAT DATE_DEBUT DATE_FIN TYPE'.split())
    META_CHRONICLE_TAGS = set("""
        NUM NUM_SEQUENCE NOR DATE_PUBLI DATE_TEXTE DERNIERE_MODIFICATION
        ORIGINE_PUBLI PAGE_DEB_PUBLI PAGE_FIN_PUBLI
    """.split())
    META_VERSION_TAGS = set(
        'TITRE TITREFULL ETAT DATE_DEBUT DATE_FIN AUTORITE MINISTERE'.split()
    )
    TABLES_MAP = {'ARTI': 'articles', 'SCTA': 'sections', 'TEXT': 'textes_'}
    TYPELIEN_MAP = {
        "ABROGATION": "ABROGE",
        "ANNULATION": "ANNULE",
        "CODIFICATION": "CODIFIE",
        "CONCORDANCE": "CONCORDE",
        "CREATION": "CREE",
        "DEPLACE": "DEPLACEMENT",
        "DISJOINT": "DISJONCTION",
        "MODIFICATION": "MODIFIE",
        "PEREMPTION": "PERIME",
        "RATIFICATION": "RATIFIE",
        "TRANSFERE": "TRANSFERT",
    }
    TYPELIEN_MAP.update([(v, k) for k, v in TYPELIEN_MAP.items()])

    # Define some shortcuts
    attr = etree._Element.get
    insert = db.insert
    update = db.update

    def get_table(parts):
        table = TABLES_MAP[parts[-1][4:8]]
        if table == 'textes_':
            table += parts[13] + 's'
        return table

    counts = {}
    def count_one(k):
        try:
            counts[k] += 1
        except KeyError:
            counts[k] = 1

    skipped = 0
    unknown_folders = {}
    liste_suppression = []
    xml = etree.XMLParser(remove_blank_text=True)
    with libarchive.file_reader(archive_path) as archive:
        for entry in tqdm(archive):
            path = entry.pathname
            if path[-1] == '/':
                continue
            parts = path.split('/')
            if parts[-1] == 'liste_suppression_legi.dat':
                liste_suppression += b''.join(entry.get_blocks()).decode('ascii').split()
                continue
            if parts[1] == 'legi':
                path = path[len(parts[0])+1:]
                parts = parts[1:]
            if not parts[2].startswith('code_et_TNC_'):
                # https://github.com/Legilibre/legi.py/issues/23
                try:
                    unknown_folders[parts[2]] += 1
                except KeyError:
                    unknown_folders[parts[2]] = 1
                continue
            dossier = parts[3]
            text_cid = parts[11]
            text_id = parts[-1][:-4]
            mtime = entry.mtime

            # Skip the file if it hasn't changed, store it if it's a duplicate
            duplicate = False
            table = get_table(parts)
            prev_row = db.one("""
                SELECT mtime, dossier, cid
                  FROM {0}
                 WHERE id = ?
            """.format(table), (text_id,))
            if prev_row:
                prev_mtime, prev_dossier, prev_cid = prev_row
                if prev_dossier != dossier or prev_cid != text_cid:
                    if prev_mtime >= mtime:
                        duplicate = True
                    else:
                        prev_row_dict = db.one("""
                            SELECT *
                              FROM {0}
                             WHERE id = ?
                        """.format(table), (text_id,), to_dict=True)
                        data = {table: prev_row_dict}
                        data['liens'] = list(db.all("""
                            SELECT *
                              FROM liens
                             WHERE src_id = ? AND NOT _reversed
                                OR dst_id = ? AND _reversed
                        """, (text_id, text_id), to_dict=True))
                        if table == 'sections':
                            data['sommaires'] = list(db.all("""
                                SELECT *
                                  FROM sommaires
                                 WHERE cid = ?
                                   AND parent = ?
                                   AND _source = 'section_ta_liens'
                            """, (text_id, text_id), to_dict=True))
                        elif table == 'textes_structs':
                            source = 'struct/' + text_id
                            data['sommaires'] = list(db.all("""
                                SELECT *
                                  FROM sommaires
                                 WHERE cid = ?
                                   AND _source = ?
                            """, (text_cid, source), to_dict=True))
                        data = {k: v for k, v in data.items() if v}
                        insert('duplicate_files', {
                            'id': text_id,
                            'sous_dossier': SOUS_DOSSIER_MAP[table],
                            'cid': prev_cid,
                            'dossier': prev_dossier,
                            'mtime': prev_mtime,
                            'data': json.dumps(data),
                            'other_cid': text_cid,
                            'other_dossier': dossier,
                            'other_mtime': mtime,
                        }, replace=True)
                        count_one('upsert into duplicate_files')
                elif prev_mtime == mtime:
                    skipped += 1
                    continue

            xml.feed(b''.join(entry.get_blocks()))
            root = xml.close()
            tag = root.tag
            meta = root.find('META')

            # Check the ID
            if tag == 'SECTION_TA':
                assert root.find('ID').text == text_id
            else:
                meta_commun = meta.find('META_COMMUN')
                assert meta_commun.find('ID').text == text_id
                nature = meta_commun.find('NATURE').text

            # Extract the data we want
            attrs = {}
            liens = ()
            sommaires = ()
            if tag == 'ARTICLE':
                assert nature == 'Article'
                assert table == 'articles'
                contexte = root.find('CONTEXTE/TEXTE')
                assert attr(contexte, 'cid') == text_cid
                sections = contexte.findall('.//TITRE_TM')
                if sections:
                    attrs['section'] = attr(sections[-1], 'id')
                meta_article = meta.find('META_SPEC/META_ARTICLE')
                scrape_tags(attrs, meta_article, META_ARTICLE_TAGS)
                scrape_tags(attrs, root, ARTICLE_TAGS, unwrap=True)
            elif tag == 'SECTION_TA':
                assert table == 'sections'
                scrape_tags(attrs, root, SECTION_TA_TAGS)
                section_id = text_id
                contexte = root.find('CONTEXTE/TEXTE')
                assert attr(contexte, 'cid') == text_cid
                parents = contexte.findall('.//TITRE_TM')
                if parents:
                    attrs['parent'] = attr(parents[-1], 'id')
                sommaires = [
                    {
                        'cid': text_cid,
                        'parent': section_id,
                        'element': attr(lien, 'id'),
                        'debut': attr(lien, 'debut'),
                        'fin': attr(lien, 'fin'),
                        'etat': attr(lien, 'etat'),
                        'num': attr(lien, 'num'),
                        'position': i,
                        '_source': 'section_ta_liens',
                    }
                    for i, lien in enumerate(root.find('STRUCTURE_TA'))
                ]
            elif tag == 'TEXTELR':
                assert table == 'textes_structs'
                scrape_tags(attrs, root, TEXTELR_TAGS)
                sommaires = [
                    {
                        'cid': text_cid,
                        'element': attr(lien, 'id'),
                        'debut': attr(lien, 'debut'),
                        'fin': attr(lien, 'fin'),
                        'etat': attr(lien, 'etat'),
                        'position': i,
                        '_source': 'struct/' + text_id,
                    }
                    for i, lien in enumerate(root.find('STRUCT'))
                ]
            elif tag == 'TEXTE_VERSION':
                assert table == 'textes_versions'
                attrs['nature'] = nature
                meta_spec = meta.find('META_SPEC')
                meta_chronicle = meta_spec.find('META_TEXTE_CHRONICLE')
                assert meta_chronicle.find('CID').text == text_cid
                scrape_tags(attrs, meta_chronicle, META_CHRONICLE_TAGS)
                meta_version = meta_spec.find('META_TEXTE_VERSION')
                scrape_tags(attrs, meta_version, META_VERSION_TAGS)
                scrape_tags(attrs, root, TEXTE_VERSION_TAGS, unwrap=True)
            else:
                raise Exception('unexpected tag: '+tag)

            if process_links and tag in ('ARTICLE', 'TEXTE_VERSION'):
                e = root if tag == 'ARTICLE' else meta_version
                liens_tags = e.find('LIENS')
                if liens_tags is not None:
                    liens = []
                    for lien in liens_tags:
                        typelien, sens = attr(lien, 'typelien'), attr(lien, 'sens')
                        src_id, dst_id = text_id, attr(lien, 'id')
                        if sens == 'cible':
                            assert dst_id
                            src_id, dst_id = dst_id, src_id
                            dst_cid = dst_titre = ''
                            typelien = TYPELIEN_MAP.get(typelien, typelien+'_R')
                            _reversed = True
                        else:
                            dst_cid = attr(lien, 'cidtexte')
                            dst_titre = lien.text
                            _reversed = False
                        liens.append({
                            'src_id': src_id,
                            'dst_cid': dst_cid,
                            'dst_id': dst_id,
                            'dst_titre': dst_titre,
                            'typelien': typelien,
                            '_reversed': _reversed,
                        })

            if duplicate:
                data = {table: attrs}
                if liens:
                    data['liens'] = liens
                if sommaires:
                    data['sommaires'] = sommaires
                insert('duplicate_files', {
                    'id': text_id,
                    'sous_dossier': SOUS_DOSSIER_MAP[table],
                    'cid': text_cid,
                    'dossier': dossier,
                    'mtime': mtime,
                    'data': json.dumps(data),
                    'other_cid': prev_cid,
                    'other_dossier': prev_dossier,
                    'other_mtime': prev_mtime,
                }, replace=True)
                count_one('upsert into duplicate_files')
                continue

            attrs['dossier'] = dossier
            attrs['cid'] = text_cid
            attrs['mtime'] = mtime

            if prev_row:
                # Delete the associated rows
                if tag == 'SECTION_TA':
                    db.run("""
                        DELETE FROM sommaires
                         WHERE cid = ?
                           AND parent = ?
                           AND _source = 'section_ta_liens'
                    """, (text_cid, section_id))
                    count(counts, 'delete from sommaires', db.changes())
                elif tag == 'TEXTELR':
                    db.run("""
                        DELETE FROM sommaires
                         WHERE cid = ?
                           AND _source = ?
                    """, (text_cid, 'struct/' + text_id))
                    count(counts, 'delete from sommaires', db.changes())
                if tag in ('ARTICLE', 'TEXTE_VERSION'):
                    db.run("""
                        DELETE FROM liens
                         WHERE src_id = ? AND NOT _reversed
                            OR dst_id = ? AND _reversed
                    """, (text_id, text_id))
                    count(counts, 'delete from liens', db.changes())
                if table == 'textes_versions':
                    db.run("DELETE FROM textes_versions_brutes WHERE id = ?", (text_id,))
                    count(counts, 'delete from textes_versions_brutes', db.changes())
                # Update the row
                count_one('update in '+table)
                update(table, dict(id=text_id), attrs)
            else:
                count_one('insert into '+table)
                attrs['id'] = text_id
                insert(table, attrs)

            # Insert the associated rows
            for lien in liens:
                db.insert('liens', lien)
            count(counts, 'insert into liens', len(liens))
            for sommaire in sommaires:
                db.insert('sommaires', sommaire)
            count(counts, 'insert into sommaires', len(sommaires))

    print("made", sum(counts.values()), "changes in the database:",
          json.dumps(counts, indent=4, sort_keys=True))

    if skipped:
        print("skipped", skipped, "files that haven't changed")

    if unknown_folders:
        for d, x in unknown_folders.items():
            print("skipped", x, "files in unknown folder `%s`" % d)

    if liste_suppression:
        suppress(get_table, db, liste_suppression)


def main():
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('directory')
    p.add_argument('--anomalies', action='store_true', default=False,
                   help="detect anomalies after each processed archive")
    p.add_argument('--anomalies-dir', default='.')
    p.add_argument('--pragma', action='append', default=[],
                   help="Doc: https://www.sqlite.org/pragma.html | Example: journal_mode=WAL")
    p.add_argument('--raw', default=False, action='store_true')
    p.add_argument('--skip-links', default=False, action='store_true',
                   help="if set, all link metadata will be ignored (the `liens` table will be empty)")
    args = p.parse_args()

    if not os.path.isdir(args.anomalies_dir):
        os.mkdir(args.anomalies_dir)

    db = connect_db(args.db, pragmas=args.pragma)
    last_update = db.one("SELECT value FROM db_meta WHERE key = 'last_update'")

    # Check and record the data mode
    db_meta_raw = db.one("SELECT value FROM db_meta WHERE key = 'raw'")
    if args.raw:
        versions_brutes = bool(db.one("SELECT 1 FROM textes_versions_brutes LIMIT 1"))
        data_is_not_raw = versions_brutes or db_meta_raw is False
        if data_is_not_raw:
            print("!> Can't honor --raw option, the data has already been modified previously.")
            raise SystemExit(1)
    if db_meta_raw != args.raw:
        db.insert('db_meta', dict(key='raw', value=args.raw), replace=True)

    # Handle the --skip-links option
    has_links = bool(db.one("SELECT 1 FROM liens LIMIT 1"))
    if not args.skip_links and not has_links and last_update is not None:
        args.skip_links = True
        print("> Warning: links will not be processed because this DB was built with --skip-links.")
    elif args.skip_links and has_links:
        print("> Deleting links...")
        db.run("DELETE FROM liens")

    # Look for new archives in the given directory
    print("> last_update is", last_update)
    archive_re = re.compile(r'(.+_)?legi(?P<global>_global)?_(?P<date>[0-9]{8}-[0-9]{6})\..+', flags=re.IGNORECASE)
    skipped = 0
    archives = sorted([
        (m.group('date'), bool(m.group('global')), m.group(0)) for m in [
            archive_re.match(fn) for fn in os.listdir(args.directory)
            if fnmatch(fn.lower(), '*legi_*.tar.*')
        ]
    ])
    most_recent_global = [t[0] for t in archives if t[1]][-1]
    if last_update and most_recent_global > last_update:
        print("> There is a new global archive, recreating the DB from scratch!")
        db.close()
        os.rename(db.address, db.address + '.back')
        db = connect_db(args.db, pragmas=args.pragma)
    archives, skipped = partition(
        archives, lambda t: t[0] >= most_recent_global and t[0] > (last_update or '')
    )
    if skipped:
        print("> Skipped %i old archives" % len(skipped))

    # Process the new archives
    for archive_date, is_global, archive_name in archives:
        print("> Processing %s..." % archive_name)
        with db:
            process_archive(db, args.directory + '/' + archive_name, not args.skip_links)
            if last_update:
                db.run("UPDATE db_meta SET value = ? WHERE key = 'last_update'", (archive_date,))
            else:
                db.run("INSERT INTO db_meta VALUES ('last_update', ?)", (archive_date,))
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
    try:
        main()
    except KeyboardInterrupt:
        pass
