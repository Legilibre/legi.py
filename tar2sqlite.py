"""
Extracts a LEGI tar archive into an SQLite DB
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from sqlite3 import OperationalError

import libarchive
from lxml import etree

from utils import connect_db


def innerHTML(e):
    i = len(e.tag) + 2
    return etree.tostring(e, encoding='unicode', with_tail=False)[i:-i-1]


def scrape_tags(attrs, root, wanted_tags, unwrap=False):
    attrs.update(
        (e.tag.lower(), (innerHTML(e[0]) if unwrap else innerHTML(e)) or None)
        for e in root if e.tag in wanted_tags
    )


def make_schema(db):
    db.executescript("""

        CREATE TABLE textes_versions
        ( id char(20) unique not null
        , nature text
        , titre text
        , titrefull text
        , etat text
        , date_debut day
        , date_fin day
        , autorite text
        , ministere text
        , num text
        , num_sequence int
        , nor char(12)
        , date_publi day
        , date_texte day
        , derniere_modification day
        , origine_publi text
        , page_deb_publi int
        , page_fin_publi int
        , visas text
        , signataires text
        , tp text
        , nota text
        , abro text
        , rect text
        , dossier text not null
        , cid char(20) not null
        , mtime int not null
        );

        CREATE TABLE sections
        ( id char(20) unique not null
        , titre_ta text
        , commentaire text
        , parent char(20) -- REFERENCES sections(id)
        , dossier text not null
        , cid char(20) not null
        , mtime int not null
        );

        CREATE TABLE articles
        ( id char(20) unique not null
        , section char(20) -- REFERENCES sections(id)
        , num text
        , etat text
        , date_debut day
        , date_fin day
        , type text
        , nota text
        , bloc_textuel text
        , dossier text not null
        , cid char(20) not null
        , mtime int not null
        );

        CREATE TABLE sections_articles
        ( section char(20) not null -- REFERENCES sections(id)
        , id char(20) not null -- REFERENCES articles(id)
        , num text not null
        , debut day
        , fin day
        , etat text
        , UNIQUE (section, id)
        );

        CREATE TABLE liens
        ( src_id char(20) not null
        , dst_cid char(20)
        , dst_id char(20)
        , dst_titre text
        , typelien text
        , _reversed bool -- to support incremental updates
        , CHECK (length(dst_cid) > 0 OR length(dst_id) > 0 OR length(dst_titre) > 0)
        );

        CREATE INDEX liens_src_idx ON liens (src_id) WHERE NOT _reversed;
        CREATE INDEX liens_dst_idx ON liens (dst_id) WHERE _reversed;

    """)


def suppress(TABLES_MAP, db, liste_suppression):
    deleted = 0
    for path in liste_suppression:
        parts = path.split('/')
        assert parts[0] == 'legi'
        if parts[13] == 'struct':
            continue
        text_id = parts[-1]
        assert len(text_id) == 20
        table = TABLES_MAP[text_id[4:8]]
        db.run("""
            DELETE FROM {0}
             WHERE dossier = ?
               AND cid = ?
               AND id = ?
        """.format(table), (parts[3], parts[11], text_id))
        deleted += db.changes()
    print('deleted', deleted, 'rows')


def main(db, archive_path):

    # Define some constants
    ARTICLE_TAGS = set('NOTA BLOC_TEXTUEL'.split())
    SECTION_TA_TAGS = set('TITRE_TA COMMENTAIRE'.split())
    TEXTE_VERSION_TAGS = set('VISAS SIGNATAIRES TP NOTA ABRO RECT'.split())
    META_ARTICLE_TAGS = set('NUM ETAT DATE_DEBUT DATE_FIN TYPE'.split())
    META_CHRONICLE_TAGS = set("""
        NUM NUM_SEQUENCE NOR DATE_PUBLI DATE_TEXTE DERNIERE_MODIFICATION
        ORIGINE_PUBLI PAGE_DEB_PUBLI PAGE_FIN_PUBLI
    """.split())
    META_VERSION_TAGS = set(
        'TITRE TITREFULL ETAT DATE_DEBUT DATE_FIN AUTORITE MINISTERE'.split()
    )
    TABLES_MAP = {'ARTI': 'articles', 'SCTA': 'sections', 'TEXT': 'textes_versions'}
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

    # Create the DB schema if necessary
    try:
        db.run("SELECT 1 FROM textes_versions LIMIT 1")
    except OperationalError:
        make_schema(db)

    # Define some shortcuts
    attr = etree._Element.get
    insert = db.insert
    update = db.update

    skipped = 0
    inserted = 0
    updated = 0
    liste_suppression = []
    xml = etree.XMLParser(remove_blank_text=True)
    with libarchive.file_reader(archive_path) as archive:
        for entry in archive:
            path = entry.pathname
            if path[-1] == '/':
                continue
            parts = path.split('/')
            if parts[-1] == 'liste_suppression_legi.dat':
                liste_suppression += b''.join(entry.get_blocks()).decode('ascii').split()
                continue
            if parts[1] == 'legi':
                parts = parts[1:]
            if parts[13] == 'struct':
                continue
            dossier = parts[3]
            text_cid = parts[11]
            text_id = parts[-1][:-4]
            mtime = entry.mtime

            table = TABLES_MAP[text_id[4:8]]
            prev_mtime = db.one("""
                SELECT mtime
                  FROM {0}
                 WHERE id = ?
            """.format(table), (text_id,)) or 0
            if prev_mtime >= mtime:
                skipped += 1
                continue

            for block in entry.get_blocks():
                xml.feed(block)
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
                contexte = root.find('CONTEXTE/TEXTE')
                assert attr(contexte, 'cid') == text_cid
                parents = contexte.findall('.//TITRE_TM')
                if parents:
                    attrs['parent'] = attr(parents[-1], 'id')
                if prev_mtime:
                    db.run("DELETE FROM sections_articles WHERE section = ?",
                           (text_id,))
                for lien_art in root.findall('STRUCTURE_TA/LIEN_ART'):
                    insert('sections_articles', {
                        'section': text_id,
                        'id': attr(lien_art, 'id'),
                        'num': attr(lien_art, 'num'),
                        'debut': attr(lien_art, 'debut'),
                        'fin': attr(lien_art, 'fin'),
                        'etat': attr(lien_art, 'etat'),
                    })
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

            if tag in ('ARTICLE', 'TEXTE_VERSION'):
                if prev_mtime:
                    db.run("""
                        DELETE FROM liens
                         WHERE src_id = ? AND NOT _reversed
                            OR dst_id = ? AND _reversed
                    """, (text_id, text_id))
                e = root if tag == 'ARTICLE' else meta_version
                liens = e.find('LIENS')
                if liens is not None:
                    for lien in liens:
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
                        insert('liens', {
                            'src_id': src_id,
                            'dst_cid': dst_cid,
                            'dst_id': dst_id,
                            'dst_titre': dst_titre,
                            'typelien': typelien,
                            '_reversed': _reversed,
                        })

            attrs['dossier'] = dossier
            attrs['cid'] = text_cid
            attrs['mtime'] = mtime

            if prev_mtime:
                updated += 1
                update(table, dict(id=text_id), attrs)
            else:
                inserted += 1
                attrs['id'] = text_id
                insert(table, attrs)

    print('skipped', skipped, 'old files')
    print('inserted', inserted, 'rows')
    print('updated', updated, 'rows')

    if liste_suppression:
        suppress(TABLES_MAP, db, liste_suppression)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('archive')
    p.add_argument('db')
    args = p.parse_args()

    db = connect_db(args.db)
    try:
        with db:
            main(db, args.archive)
    except KeyboardInterrupt:
        pass
