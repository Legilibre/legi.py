import json
from collections import defaultdict
from lxml import etree
from .constants import ARTICLE_TAGS, SECTION_TA_TAGS, TEXTELR_TAGS, \
    TEXTE_VERSION_TAGS, META_ARTICLE_TAGS, META_CHRONICLE_TAGS, META_CONTENEUR_TAGS, \
    META_VERSION_TAGS, SOUS_DOSSIER_MAP, TYPELIEN_MAP, TM_TAGS
from dila2sql.models import Calipso, DuplicateFile, ArticleCalipso, \
    TexteVersionBrute, Lien, Tetier, Conteneur, Sommaire, TABLE_TO_MODEL
from dila2sql.utils import json_serializer


attr = etree._Element.get


def innerHTML(e):
    r = etree.tostring(e, encoding='unicode', with_tail=False)
    return r[r.find('>')+1:-len(e.tag)-3]


def scrape_tags(attrs, root, wanted_tags, unwrap=False):
    attrs.update(
        (e.tag.lower(), (innerHTML(e[0]) if unwrap else innerHTML(e)) or None)
        for e in root if e.tag in wanted_tags
    )


def process_xml(
    xml_blob,
    mtime,
    base,
    table,
    dossier,
    text_cid,
    text_id,
    process_links
):
    # TODO
    skipped = 0
    counts = defaultdict(lambda: 0)

    # Parse the XML blob
    xml = etree.XMLParser(remove_blank_text=True)
    xml.feed(xml_blob)
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
        for calipso in current_calipsos:
            Calipso.insert(id=calipso).on_conflict_ignore().execute()
        counts['insert into calipsos'] += len(current_calipsos)
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

    return counts, skipped
