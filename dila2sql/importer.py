"""
Imports LEGI tar archives into an SQL DB
"""

from argparse import ArgumentParser
from fnmatch import fnmatch
import json
import os
import re
from collections import defaultdict

import libarchive
from lxml import etree

try:
    from tqdm import tqdm
except ImportError:
    print('[warning] tqdm is not installed, the progress bar is disabled')
    tqdm = lambda x: x

from .anomalies import detect_anomalies
from .utils import connect_db, partition, json_serializer
from .models import db_proxy, DBMeta, Calipso, DuplicateFile, \
    ArticleCalipso, TexteVersionBrute, Tetier, \
    Conteneur, Lien, Sommaire, TABLE_TO_MODEL


TABLES_MAP = {'ARTI': 'articles', 'SCTA': 'sections', 'TEXT': 'textes_', 'CONT': 'conteneurs'}
ARTICLE_TAGS = set('NOTA BLOC_TEXTUEL'.split())
SECTION_TA_TAGS = set('TITRE_TA COMMENTAIRE'.split())
TEXTELR_TAGS = set('VERSIONS'.split())
TEXTE_VERSION_TAGS = set('VISAS SIGNATAIRES TP NOTA ABRO RECT'.split())
META_ARTICLE_TAGS = set('NUM ETAT DATE_DEBUT DATE_FIN TYPE TITRE'.split())
META_CHRONICLE_TAGS = set("""
    NUM NUM_SEQUENCE NOR DATE_PUBLI DATE_TEXTE DERNIERE_MODIFICATION
    ORIGINE_PUBLI PAGE_DEB_PUBLI PAGE_FIN_PUBLI
""".split())
META_CONTENEUR_TAGS = set('TITRE ETAT NUM DATE_PUBLI'.split())
META_VERSION_TAGS = set(
    'TITRE TITREFULL ETAT DATE_DEBUT DATE_FIN AUTORITE MINISTERE'.split()
)
SOUS_DOSSIER_MAP = {
    'articles': 'article',
    'sections': 'section_ta',
    'textes_structs': 'texte/struct',
    'textes_versions': 'texte/version',
    'conteneurs': 'conteneur'
}
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
TM_TAGS = ['TITRE_TM']


attr = etree._Element.get


def get_table(parts):
    if parts[-1][4:8] not in TABLES_MAP:
        return None
    table = TABLES_MAP[parts[-1][4:8]]
    if table == 'textes_':
        if parts[0] == 'legi':
            table += parts[13] + 's'
        elif parts[0] == 'jorf':
            table += parts[3] + 's'
        elif parts[0] == 'kali':
            table += parts[3] + 's'
    return table


def innerHTML(e):
    r = etree.tostring(e, encoding='unicode', with_tail=False)
    return r[r.find('>')+1:-len(e.tag)-3]


def scrape_tags(attrs, root, wanted_tags, unwrap=False):
    attrs.update(
        (e.tag.lower(), (innerHTML(e[0]) if unwrap else innerHTML(e)) or None)
        for e in root if e.tag in wanted_tags
    )


def suppress(base, db, liste_suppression):
    counts = defaultdict(lambda: 0)
    for path in liste_suppression:
        parts = path.split('/')
        if parts[0] != base.lower():
            print('[warning] cannot suppress {0}'.format(path))
            continue
        text_id = parts[-1]
        text_cid = parts[11] if base == 'LEGI' else text_id
        assert len(text_id) == 20

        table = get_table(parts)
        model = TABLE_TO_MODEL[table]
        if model == Conteneur:
            deleted_rows = Conteneur.delete().where(Conteneur.id == text_id).execute()
        else:
            deleted_rows = model.delete().where(
                (model.dossier == parts[3]) &
                (model.cid == text_cid) &
                (model.id == text_id)
            ).execute()

        if deleted_rows:
            counts['delete from ' + table] += deleted_rows
            # Also delete derivative data
            if table in ('articles', 'textes_versions'):
                deleted_subrows = Lien.delete().where(
                    ((Lien.src_id == text_id) & (~ Lien._reversed)) |
                    ((Lien.dst_id == text_id) & (Lien._reversed))
                ).execute()
                counts['delete from liens'] += deleted_subrows
            if table in ('articles'):
                deleted_subrows = ArticleCalipso.delete() \
                    .where(ArticleCalipso.article_id == text_id) \
                    .execute()
                counts['delete from articles_calipsos'] += deleted_subrows
            elif table == 'sections':
                deleted_subrows = Sommaire.delete().where(
                    (Sommaire.parent == text_id) &
                    (Sommaire._source == 'section_ta_liens')
                ).execute()
                counts['delete from sommaires'] += deleted_subrows
            elif table == 'textes_structs':
                deleted_subrows = Sommaire.delete().where(
                    (Sommaire.parent == text_id) &
                    (Sommaire._source == "struct/%s" % text_id)
                ).execute()
                counts['delete from sommaires'] += deleted_subrows
            elif table == "conteneurs":
                deleted_subrows = Sommaire.delete() \
                    .where(Sommaire._source == text_id) \
                    .execute()
                counts['delete from sommaires'] += 1
            # And delete the associated row in textes_versions_brutes if it exists
            if table == 'textes_versions':
                deleted_subrows = TexteVersionBrute.delete() \
                    .where(TexteVersionBrute.id == text_id) \
                    .execute()
                counts['delete from textes_versions_brutes'] += deleted_subrows
            # If the file had an older duplicate that hasn't been deleted then
            # we have to fall back to that, otherwise we'd be missing data
            duplicate_files = DuplicateFile.select() \
                .where(DuplicateFile.id == 'KALIARTI000026951576a') \
                .order_by(DuplicateFile.mtime.desc()) \
                .limit(1) \
                .dicts()
            older_file = duplicate_files[0] if len(duplicate_files) > 0 else None

            if older_file:
                deleted_duplicate_files = DuplicateFile.delete().where(
                    (DuplicateFile.dossier == older_file['dossier']) &
                    (DuplicateFile.cid == older_file['cid']) &
                    (DuplicateFile.id == older_file['id'])
                ).execute()
                counts['delete from duplicate_files'] += deleted_duplicate_files
                for table, rows in json.loads(older_file['data']).items():
                    model = TABLE_TO_MODEL[table]
                    if isinstance(rows, dict):
                        rows['id'] = older_file['id']
                        rows['cid'] = older_file['cid']
                        rows['dossier'] = older_file['dossier']
                        rows['mtime'] = older_file['mtime']
                        rows = (rows,)
                    for row in rows:
                        model.create(**row)
                    counts['insert into ' + table] += len(rows)
        else:
            # Remove the file from the duplicates table if it was in there
            deleted_duplicate_files = DuplicateFile.delete().where(
                (DuplicateFile.dossier == parts[3]) &
                (DuplicateFile.cid == text_cid) &
                (DuplicateFile.id == text_id)
            ).execute()
            counts['delete from duplicate_files'] += deleted_duplicate_files
    total = sum(counts.values())
    print("made", total, "changes in the database based on liste_suppression_"+base.lower()+".dat:",
          json.dumps(counts, indent=4, sort_keys=True))


def process_file(
    xml, entry, base, unknown_folders, counts,
    liste_suppression, calipsos, process_links, skipped
):
    path = entry.pathname
    if path[-1] == '/':
        return
    parts = path.split('/')
    if parts[-1] == 'liste_suppression_'+base.lower()+'.dat':
        liste_suppression += b''.join(entry.get_blocks()).decode('ascii').split()
        return
    if parts[1] == base.lower():
        path = path[len(parts[0])+1:]
        parts = parts[1:]
    if (
        parts[0] not in ['legi', 'jorf', 'kali'] or
        (parts[0] == 'legi' and not parts[2].startswith('code_et_TNC_')) or
        (parts[0] == 'jorf' and parts[2] not in ['article', 'section_ta', 'texte']) or
        (parts[0] == 'kali' and parts[2] not in ['article', 'section_ta', 'texte', 'conteneur'])
    ):
        # https://github.com/Legilibre/legi.py/issues/23
        unknown_folders[parts[2]] += 1
        return
    dossier = parts[3] if base == 'LEGI' else None
    text_cid = parts[11] if base == 'LEGI' else None
    text_id = parts[-1][:-4]
    mtime = entry.mtime

    # Read the file
    xml.feed(b''.join(entry.get_blocks()))
    root = xml.close()
    tag = root.tag
    meta = root.find('META')

    # Obtain the CID when database is not LEGI
    if base != 'LEGI':
        if tag in ['ARTICLE', 'SECTION_TA']:
            contexte = root.find('CONTEXTE/TEXTE')
            text_cid = attr(contexte, 'cid')
        elif tag in ['TEXTELR', 'TEXTE_VERSION', 'TEXTEKALI']:
            meta_spec = meta.find('META_SPEC')
            meta_chronicle = meta_spec.find('META_TEXTE_CHRONICLE')
            text_cid = meta_chronicle.find('CID').text
        elif tag in ["IDCC"]:
            text_cid = None
        else:
            raise Exception('unexpected tag: '+tag)

    # Skip the file if it hasn't changed, store it if it's a duplicate
    duplicate = False
    table = get_table(parts)
    if table is None:
        unknown_folders[text_id] += 1
        return

    if table == 'conteneurs':
        prev_rows = Conteneur \
            .select() \
            .where(Conteneur.id == text_id) \
            .dicts().limit(1)
        prev_row = prev_rows[0] if len(prev_rows) > 0 else None
        if prev_row:
            prev_row["dossier"] = None
            prev_row["cid"] = None
    else:
        model = TABLE_TO_MODEL[table]
        prev_rows = model \
            .select(model.mtime, model.dossier, model.cid) \
            .where(model.id == text_id) \
            .dicts().limit(1)
        prev_row = prev_rows[0] if len(prev_rows) > 0 else None
    if prev_row:
        if prev_row["dossier"] != dossier or prev_row["cid"] != text_cid:
            if prev_row["mtime"] >= mtime:
                duplicate = True
            else:
                if table != 'conteneurs':
                    model = TABLE_TO_MODEL[table]
                    prev_row = model.select().where(model.id == text_id).dicts().get()
                data = {table: prev_row}
                data['liens'] = list(
                    Lien.select().where(
                        ((Lien.src_id == text_id) & (~ Lien._reversed)) |
                        ((Lien.dst_id == text_id) & (Lien._reversed))
                    ).dicts()
                )
                if table == 'sections':
                    data['sommaires'] = list(
                        Sommaire.select().where(
                            (Sommaire.parent == text_id) &
                            (Sommaire._source == 'section_ta_liens')
                        ).dicts()
                    )
                elif table == 'textes_structs':
                    data['sommaires'] = list(
                        Sommaire.select()
                            .where(Sommaire._source == "struct/%s" % text_id)
                            .dicts()
                    )
                data = {k: v for k, v in data.items() if v}
                DuplicateFile.insert(
                    id=text_id,
                    sous_dossier=SOUS_DOSSIER_MAP[table],
                    cid=prev_row["cid"],
                    dossier=prev_row["dossier"],
                    mtime=prev_row["mtime"],
                    data=json.dumps(data, default=json_serializer),
                    other_cid=text_cid,
                    other_dossier=dossier,
                    other_mtime=mtime,
                ).on_conflict(
                    conflict_target=[
                        DuplicateFile.id,
                        DuplicateFile.sous_dossier,
                        DuplicateFile.cid,
                        DuplicateFile.dossier
                    ],
                    preserve=[
                        DuplicateFile.mtime,
                        DuplicateFile.data,
                        DuplicateFile.other_cid,
                        DuplicateFile.other_dossier,
                        DuplicateFile.other_mtime,
                    ]
                ).execute()
                counts['upsert into duplicate_files'] += 1
        elif prev_row["mtime"] == mtime:
            skipped += 1
            return

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
    tetiers = []
    articles_calipsos = []
    if tag == 'ARTICLE':
        assert nature == 'Article'
        assert table == 'articles'
        article_id = text_id
        contexte = root.find('CONTEXTE/TEXTE')
        assert attr(contexte, 'cid') == text_cid
        sections = contexte.findall('.//TITRE_TM')
        if sections:
            attrs['section'] = attr(sections[-1], 'id')
        meta_article = meta.find('META_SPEC/META_ARTICLE')
        scrape_tags(attrs, meta_article, META_ARTICLE_TAGS)
        scrape_tags(attrs, root, ARTICLE_TAGS, unwrap=True)
        current_calipsos = [innerHTML(c) for c in meta_article.findall('CALIPSOS/CALIPSO')]
        calipsos |= set(current_calipsos)
        articles_calipsos += [
            {'article_id': article_id, 'calipso_id': c} for c in current_calipsos
        ]

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
    elif tag in ['TEXTELR', 'TEXTEKALI']:
        assert table == 'textes_structs'
        meta_spec = meta.find('META_SPEC')
        meta_chronicle = meta_spec.find('META_TEXTE_CHRONICLE')
        assert meta_chronicle.find('CID').text == text_cid
        scrape_tags(attrs, root, TEXTELR_TAGS)
        sommaires = [
            {
                'parent': text_id,
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
    elif tag == 'IDCC':
        assert table == 'conteneurs'
        attrs['nature'] = nature
        meta_spec = meta.find('META_SPEC')
        meta_conteneur = meta_spec.find('META_CONTENEUR')
        scrape_tags(attrs, meta_conteneur, META_CONTENEUR_TAGS)
        sommaires = []
        for i, tm in enumerate(root.find('STRUCTURE_TXT')):
            lien_txts = tm.find('LIEN_TXT')
            if lien_txts is not None:
                tetier_id = "KALITM%s-%s" % (text_id[8:], i)
                sommaires.append(
                    {
                        'parent': text_id,
                        'element': tetier_id,
                        'debut': attr(tm, 'debut'),
                        'fin': attr(tm, 'fin'),
                        'etat': attr(tm, 'etat'),
                        'position': i,
                        '_source': text_id,
                    }
                )
                tetier = {
                    'id': tetier_id,
                    'niv': int(attr(tm, 'niv')),
                    'conteneur_id': text_id
                }
                scrape_tags(tetier, tm, TM_TAGS)
                tetiers.append(tetier)
                for y, child in enumerate(tm):
                    if child.tag == 'TITRE_TM':
                        continue
                    elif child.tag == 'LIEN_TXT':
                        sommaires.append({
                            'parent': tetier_id,
                            'element': attr(child, 'idtxt'),
                            'position': y,
                            '_source': text_id
                        })
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

        DuplicateFile.insert(
            id=text_id,
            sous_dossier=SOUS_DOSSIER_MAP[table],
            cid=text_cid,
            dossier=dossier,
            mtime=mtime,
            data=json.dumps(data, default=json_serializer),
            other_cid=prev_row["cid"],
            other_dossier=prev_row["dossier"],
            other_mtime=prev_row["mtime"],
        ).on_conflict(
            conflict_target=[
                DuplicateFile.id,
                DuplicateFile.sous_dossier,
                DuplicateFile.cid,
                DuplicateFile.dossier
            ],
            preserve=[
                DuplicateFile.mtime,
                DuplicateFile.data,
                DuplicateFile.other_cid,
                DuplicateFile.other_dossier,
                DuplicateFile.other_mtime,
            ]
        ).execute()
        counts['upsert into duplicate_files'] += 1
        return

    if table != 'conteneurs':
        attrs['dossier'] = dossier
        attrs['cid'] = text_cid
    attrs['mtime'] = mtime

    if prev_row:
        # Delete the associated rows
        if tag == 'SECTION_TA':
            deleted_linked_rows = Sommaire.delete().where(
                (Sommaire.parent == section_id) &
                (Sommaire._source == 'section_ta_liens')
            ).execute()
            counts['delete from sommaires'] += deleted_linked_rows
        elif tag in ['TEXTELR', 'TEXTEKALI']:
            deleted_linked_rows = Sommaire.delete() \
                .where(Sommaire._source == 'struct/%s' % text_id) \
                .execute()
            counts['delete from sommaires'] += deleted_linked_rows
        elif tag == 'IDCC':
            deleted_linked_rows = Sommaire.delete() \
                .where(Sommaire._source == text_id) \
                .execute()
            counts['delete from sommaires'] += deleted_linked_rows
            deleted_linked_rows = Tetier.delete() \
                .where(Tetier.conteneur_id == text_id) \
                .execute()
            counts['delete from tetiers'] += deleted_linked_rows
        if tag in ('ARTICLE', 'TEXTE_VERSION'):
            deleted_linked_rows = Lien.delete().where(
                ((Lien.src_id == text_id) & (~ Lien._reversed)) |
                ((Lien.dst_id == text_id) & (Lien._reversed))
            ).execute()
            counts['delete from liens'] += deleted_linked_rows
        if tag in ('ARTICLE'):
            deleted_linked_rows = ArticleCalipso.delete() \
                .where(ArticleCalipso.article_id == text_id) \
                .execute()
            counts['delete from articles_calipsos'] += deleted_linked_rows
        if table == 'textes_versions':
            deleted_linked_rows = TexteVersionBrute.delete() \
                .where(TexteVersionBrute.id == text_id) \
                .execute()
            counts['delete from textes_versions_brutes'] += deleted_linked_rows
        # Update the row
        counts['update in '+table] += 1
        model = TABLE_TO_MODEL[table]
        model.update(**attrs).where(model.id == text_id).execute()
    else:
        counts['insert into '+table] += 1
        attrs['id'] = text_id
        model = TABLE_TO_MODEL[table]
        model.create(**attrs)

    # Insert the associated rows
    for lien in liens:
        Lien.create(**lien)
    counts['insert into liens'] += len(liens)

    for sommaire in sommaires:
        Sommaire.create(**sommaire)
    counts['insert into sommaires'] += len(sommaires)

    for tetier in tetiers:
        Tetier.create(**tetier)
    counts['insert into tetiers'] += len(tetiers)

    for article_calipso in articles_calipsos:
        ArticleCalipso.create(**article_calipso)
    counts['insert into articles_calipsos'] += len(articles_calipsos)


def process_archive(db, archive_path, process_links=True):
    counts = defaultdict(lambda: 0)
    base = DBMeta.get(DBMeta.key == 'base').value or 'LEGI'
    skipped = 0
    unknown_folders = defaultdict(lambda: 0)
    liste_suppression = []
    calipsos = set()
    xml = etree.XMLParser(remove_blank_text=True)
    with libarchive.file_reader(archive_path) as archive:
        for entry in tqdm(archive):
            process_file(
                xml, entry, base, unknown_folders, counts,
                liste_suppression, calipsos, process_links, skipped
            )
            db.commit()

    for calipso in calipsos:
        Calipso.insert(id=calipso).on_conflict_ignore().execute()
    counts['insert into calipsos'] += len(calipsos)

    print(
        "made %s changes in the database:" % sum(counts.values()),
        json.dumps(counts, indent=4, sort_keys=True)
    )

    if skipped:
        print("skipped", skipped, "files that haven't changed")

    if unknown_folders:
        for d, x in unknown_folders.items():
            print("skipped", x, "files in unknown folder `%s`" % d)

    if liste_suppression:
        suppress(base, db, liste_suppression)


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
    p.add_argument('--base', choices=["LEGI", "JORF", "KALI"])
    p.add_argument('--skip-links', default=False, action='store_true',
                   help="if set, all link metadata will be ignored (the `liens` table will be empty)")
    args = p.parse_args()

    if not os.path.isdir(args.anomalies_dir):
        os.mkdir(args.anomalies_dir)

    db = connect_db(args.db)
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
        with db:
            process_archive(db, args.directory + '/' + archive_name, not args.skip_links)
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
    try:
        main()
    except KeyboardInterrupt:
        pass
