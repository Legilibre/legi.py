"""
Functions that can be used to export the data stored in SQLite to other formats.
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
import json

from .utils import connect_db


TABLES_MAP = {'ARTI': 'articles', 'SCTA': 'sections'}


def iterate_everything(db):
    textes = [r[0] for r in db.all("SELECT id FROM textes")]
    for texte_id in textes:
        for e in iterate_texte(db, texte_id):
            yield e


def iterate_texte(db, texte_id):
    versions = list(db.all("""
        SELECT cid, id
          FROM textes_versions
         WHERE texte_id = ?
      ORDER BY date_debut ASC
    """, (texte_id,), to_dict=True))
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
        sommaire = list(db.all("""
            SELECT *
              FROM sommaires
             WHERE cid = ?
               AND _source = 'struct/' || ?
          ORDER BY position DESC
        """, (cid, version['id']), to_dict=True))
        # Note: `sommaire` is in reverse order, because python lists are better
        # at adding elements at the end than at the beginning
        while True:
            try:
                s_data = sommaire.pop()
            except IndexError:
                break
            e_id = s_data['element']
            table = TABLES_MAP[e_id[4:8]]
            e_data = db.one("""
                SELECT *
                  FROM {0}
                 WHERE id = ?
            """.format(table), (e_id,), to_dict=True)
            yield (table[:-1], (s_data, e_data))
            if table == 'sections':
                sommaire.extend(db.all("""
                    SELECT *
                      FROM sommaires
                     WHERE cid = ?
                       AND parent = ?
                  ORDER BY position DESC
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
