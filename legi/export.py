"""
Functions that can be used to export the data stored in SQLite to other formats.
"""

from argparse import ArgumentParser
import json

from .db import connect_db


TYPES_MAP = {'ARTI': 'article', 'SCTA': 'section'}


def iterate_everything(db):
    textes = db.all("SELECT id FROM textes")
    for texte_id in textes:
        for e in iterate_texte(db, texte_id):
            yield e


def iterate_texte(db, texte_id):
    versions = db.list("""
        SELECT cid, id
          FROM textes_versions
         WHERE texte_id = ?
      ORDER BY date_debut ASC
    """, (texte_id,), to_dict=True)
    yield ('texte', {'temp_id': texte_id, 'versions': versions})
    for v in versions:
        for e in iterate_cid(db, v['cid']):
            yield e


def iterate_cid(db, cid):
    textes_versions = db.all("""
        SELECT *
          FROM textes_versions
         WHERE cid = ?
      ORDER BY date_debut ASC
    """, (cid,), to_dict=True)
    for version in textes_versions:
        yield ('texte_version', version)
        sommaire = db.deque("""
            SELECT *
              FROM sommaires
             WHERE cid = ?
               AND _source = 'struct/' || ?
          ORDER BY position ASC
        """, (cid, version['id']), to_dict=True)
        while True:
            try:
                s_data = sommaire.popleft()
            except IndexError:
                break
            e_id = s_data['element']
            typ = TYPES_MAP[e_id[4:8]]
            e_data = db.one("""
                SELECT *
                  FROM {0}s
                 WHERE id = ?
            """.format(typ), (e_id,), to_dict=True)
            yield (typ, (s_data, e_data))
            if typ == 'section':
                sommaire.extend(db.all("""
                    SELECT *
                      FROM sommaires
                     WHERE cid = ?
                       AND parent = ?
                  ORDER BY position ASC
                """, (cid, e_id), to_dict=True))


def main(args):
    db = connect_db(args.db)
    if args.texte:
        if not args.cid:
            raise SystemExit("--texte nécessite --cid")
        texte_id = db.one("SELECT texte_id FROM textes_versions WHERE cid = ? LIMIT 1", (args.cid,))
        stream = iterate_texte(db, texte_id)
    elif args.cid:
        stream = iterate_cid(db, args.cid)
    else:
        stream = iterate_everything(db)
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
