"""
Functions that can be used to export the data stored in SQLite to other formats.
"""

from argparse import ArgumentParser
import json

from .utils import connect_db
from .models import db_proxy, TexteVersion, Sommaire, DBMeta, TABLE_TO_MODEL


TABLES_MAP = {'ARTI': 'articles', 'SCTA': 'sections'}


def iterate_everything(db):
    textes = [r[0] for r in db.execute_sql("SELECT id FROM textes")]
    for texte_id in textes:
        for e in iterate_texte(db, texte_id):
            yield e


def iterate_texte(db, texte_id):
    versions = list(
        TexteVersion.
            select(TexteVersion.cid, TexteVersion.id).
            where(TexteVersion.texte_id == texte_id).
            order_by(TexteVersion.date_debut).
            dicts()
    )
    yield ('texte', {'temp_id': texte_id, 'versions': versions})
    for v in versions:
        for e in iterate_cid(db, v['cid']):
            yield e


def iterate_cid(db, cid):
    textes_versions = TexteVersion.select() \
        .where(TexteVersion.cid == cid) \
        .order_by(TexteVersion.date_debut) \
        .dicts()
    for version in textes_versions:
        yield ('texte_version', version)
        sommaire = list(
            Sommaire.select().
                where(Sommaire.cid == cid & Sommaire._source == "struct/%s" % version["id"]).
                order_by(Sommaire.position.desc()).
                dicts()
        )
        # Note: `sommaire` is in reverse order, because python lists are better
        # at adding elements at the end than at the beginning
        while True:
            try:
                s_data = sommaire.pop()
            except IndexError:
                break
            e_id = s_data['element']
            table = TABLES_MAP[e_id[4:8]]
            model = TABLE_TO_MODEL[table]
            e_data = model.select().where(model.id == e_id).dicts().first()
            yield (table[:-1], (s_data, e_data))
            if table == 'sections':
                sommaire.extend(list(
                    Sommaire.select().
                        where(Sommaire.cid == cid & Sommaire.parent == e_id).
                        order_by(Sommaire.position.desc()).
                        dicts()
                ))


def main(args):
    db = connect_db(args.db)
    db_proxy.initialize(db)

    db_base = DBMeta.get(key='base').value
    if db_base != "LEGI":
        print("export script can only run with LEGI databases.")
        exit(1)

    if args.texte:
        if not args.cid:
            raise SystemExit("--texte nécessite --cid")
        texte_version = TexteVersion \
            .select(TexteVersion.texte_id) \
            .where(TexteVersion.cid == args.cid) \
            .first()
        texte_id = texte_version.texte_id if texte_version else None
        stream = iterate_texte(db, texte_id)
    elif args.cid:
        stream = iterate_cid(db, args.cid)
    else:
        stream = iterate_everything(db)
    i = 0
    for i, t in enumerate(stream):
        if i >= args.limit:
            print('reached the limit (%i)' % args.limit)
            return
        e_type, e_payload = t
        if isinstance(e_payload, dict):
            e_payload = (e_payload,)
        e_payload = '\n'.join(json.dumps(o, indent=4) for o in e_payload)
        print(e_type, e_payload.replace('\n', '\n    '), sep='\n    ')
    print('end')
    print('%i elements listed' % i)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('limit', type=int)
    p.add_argument('--cid', nargs='?')
    p.add_argument('--texte', action='store_true', default=False,
                   help="active l'export de toutes les versions du texte identitifé par --cid")
    args = p.parse_args()
    main(args)
