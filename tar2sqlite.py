"""
Extracts a LEGI tar archive into an SQLite DB
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
import re
from sqlite3 import connect

import libarchive
from lxml import etree

from utils import inserter


def innerHTML(e):
    i = len(e.tag) + 2
    return etree.tostring(e, encoding='unicode', with_tail=False)[i:-i-1]


def scrape_tags(attrs, root, wanted_tags, unwrap=False):
    attrs.update(
        (e.tag.lower(), (innerHTML(e[0]) if unwrap else innerHTML(e)) or None)
        for e in root if e.tag in wanted_tags
    )


def main(conn, archive_path):

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

    # Create the DB
    conn.executescript("""

        CREATE TABLE textes_versions
        ( nature text
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
        , id char(20) not null
        , mtime int not null
        , UNIQUE (dossier, cid, id)
        );

        CREATE INDEX textes_versions_date_texte ON textes_versions (date_texte);
        CREATE INDEX textes_versions_nature_num ON textes_versions (nature, num);
        CREATE INDEX textes_versions_nor ON textes_versions (nor);
        CREATE INDEX textes_versions_titre ON textes_versions (titre);
        CREATE INDEX textes_versions_titrefull ON textes_versions (titrefull);

        CREATE TABLE sections
        ( titre_ta text
        , commentaire text
        , parent char(20) -- REFERENCES sections(id)
        , dossier text not null
        , cid char(20) not null -- REFERENCES textes_versions(id)
        , id char(20) not null
        , mtime int not null
        , UNIQUE (dossier, cid, id)
        );

        CREATE TABLE articles
        ( section char(20) -- REFERENCES sections(id)
        , num text
        , etat text
        , date_debut day
        , date_fin day
        , type text
        , nota text
        , bloc_textuel text
        , dossier text not null
        , cid char(20) not null -- REFERENCES textes_versions(id)
        , id char(20) not null
        , mtime int not null
        , UNIQUE (dossier, cid, id)
        );

        CREATE TABLE sections_articles
        ( section char(20) not null -- REFERENCES sections(id)
        , id char(20) not null -- REFERENCES articles(id)
        , num text not null
        , debut day
        , fin day
        , etat text
        , cid char(20) not null -- REFERENCES textes_versions(id)
        -- , UNIQUE (cid, section, num, debut)
        );

        CREATE TABLE liens
        ( src_cid char(20) not null
        , src_id char(20) not null
        , dst_cid char(20)
        , dst_id char(20)
        , dst_titre text
        , typelien text
        , sens text
        , CHECK (length(dst_cid) > 0 OR length(dst_id) > 0 OR length(dst_titre) > 0)
        );

    """)

    # Define some shortcuts
    attr = etree._Element.get
    insert = inserter(conn)

    xml = etree.XMLParser(remove_blank_text=True)
    with libarchive.file_reader(archive_path) as archive:
        for entry in archive:
            path = entry.pathname
            if path[-1] == '/':
                continue
            parts = path.split('/')
            if parts[13] == 'struct':
                continue
            dossier = parts[3]
            text_cid = parts[11]
            text_id = parts[-1][:-4]

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
                table = 'articles'
                contexte = root.find('CONTEXTE/TEXTE')
                assert attr(contexte, 'cid') == text_cid
                sections = contexte.findall('.//TITRE_TM')
                if sections:
                    attrs['section'] = attr(sections[-1], 'id')
                meta_article = meta.find('META_SPEC/META_ARTICLE')
                scrape_tags(attrs, meta_article, META_ARTICLE_TAGS)
                scrape_tags(attrs, root, ARTICLE_TAGS, unwrap=True)
                for lien in root.find('LIENS'):
                    insert('liens', {
                        'src_cid': text_cid,
                        'src_id': text_id,
                        'dst_cid': attr(lien, 'cidtexte'),
                        'dst_id': attr(lien, 'id'),
                        'dst_titre': lien.text,
                        'typelien': attr(lien, 'typelien'),
                        'sens': attr(lien, 'sens'),
                    })
            elif tag == 'SECTION_TA':
                table = 'sections'
                scrape_tags(attrs, root, SECTION_TA_TAGS)
                contexte = root.find('CONTEXTE/TEXTE')
                assert attr(contexte, 'cid') == text_cid
                parents = contexte.findall('.//TITRE_TM')
                if parents:
                    attrs['parent'] = attr(parents[-1], 'id')
                for lien_art in root.findall('STRUCTURE_TA/LIEN_ART'):
                    insert('sections_articles', {
                        'section': text_id,
                        'id': attr(lien_art, 'id'),
                        'num': attr(lien_art, 'num'),
                        'debut': attr(lien_art, 'debut'),
                        'fin': attr(lien_art, 'fin'),
                        'etat': attr(lien_art, 'etat'),
                        'cid': text_cid,
                    })
            elif tag == 'TEXTE_VERSION':
                table = 'textes_versions'
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

            attrs['dossier'] = dossier
            attrs['cid'] = text_cid
            attrs['id'] = text_id
            attrs['mtime'] = entry.mtime

            insert(table, attrs)


p = ArgumentParser()
p.add_argument('archive')
args = p.parse_args()

conn = connect(re.sub(r'^(/?(?:[^/]*/)*\.?[^.]+).*', r'\1.sqlite', args.archive))
try:
    main(conn, args.archive)
finally:
    conn.commit()
    conn.close()
