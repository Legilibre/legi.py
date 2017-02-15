# encoding: utf8

from __future__ import print_function, unicode_literals

from argparse import ArgumentParser

from lxml import etree

from .normalize import main as normalize
from .utils import connect_db


def connect_by_nature_num():
    db.run("""
        UPDATE textes_versions
           SET texte_id = (
                   SELECT id
                     FROM textes t
                    WHERE t.nature = textes_versions.nature
                      AND t.num = textes_versions.num
               )
         WHERE texte_id IS NULL
           AND EXISTS (
                   SELECT id
                     FROM textes t
                    WHERE t.nature = textes_versions.nature
                      AND t.num = textes_versions.num
               );
    """)
    print('connected %i rows of textes_versions based on (nature, num)' % db.changes())


def connect_by_nor():
    db.run("""
        CREATE TEMP TABLE texte_by_nor AS
            SELECT nor, min(texte_id)
              FROM textes_versions
             WHERE nor IS NOT NULL
               AND texte_id IS NOT NULL
          GROUP BY nor
            HAVING min(nature) = max(nature)
               AND min(num) = max(num)
               AND min(texte_id) = max(texte_id);
    """)
    db.run("CREATE UNIQUE INDEX texte_by_nor_index ON texte_by_nor (nor)")
    db.run("""
        UPDATE textes_versions
           SET texte_id = (
                   SELECT texte_id
                     FROM texte_by_nor t
                    WHERE t.nor = textes_versions.nor
               )
         WHERE texte_id IS NULL
           AND EXISTS (
                   SELECT texte_id
                     FROM texte_by_nor t
                    WHERE t.nor = textes_versions.nor
               );
    """)
    print('connected %i rows of textes_versions based on nor' % db.changes())
    db.run("DROP TABLE texte_by_nor")


def connect_by_titrefull_s():
    db.run("""
        CREATE TEMP TABLE texte_by_titrefull_s AS
            SELECT DISTINCT titrefull_s, texte_id
              FROM textes_versions
             WHERE texte_id IS NOT NULL;
    """)
    db.run("CREATE UNIQUE INDEX texte_by_titrefull_s_index ON texte_by_titrefull_s (titrefull_s)")
    db.run("""
        UPDATE textes_versions
           SET texte_id = (
                   SELECT texte_id
                     FROM texte_by_titrefull_s t
                    WHERE t.titrefull_s = textes_versions.titrefull_s
               )
         WHERE texte_id IS NULL
           AND EXISTS (
                   SELECT texte_id
                     FROM texte_by_titrefull_s t
                    WHERE t.titrefull_s = textes_versions.titrefull_s
               );
    """)
    print('connected %i rows of textes_versions based on titrefull_s' % db.changes())
    db.run("DROP TABLE texte_by_titrefull_s")


def factorize_by(key):
    duplicates = db.all("""
        SELECT min(nature), {0}, group_concat(texte_id)
          FROM textes_versions
         WHERE texte_id IS NOT NULL
      GROUP BY {0}
        HAVING min(texte_id) <> max(texte_id)
           AND min(nature) = max(nature)
    """.format(key))
    total = 0
    factorized = 0
    for row in duplicates:
        ids = tuple(row[2].split(','))
        uid = db.one("SELECT id FROM textes ORDER BY id DESC LIMIT 1") + 1
        if key == 'cid':
            db.run("INSERT INTO textes (id, nature) VALUES (?, ?)", (uid, row[0]))
        else:
            db.run("INSERT INTO textes (id, nature, {0}) VALUES (?, ?, ?)".format(key),
                   (uid, row[0], row[1]))
        db.run("""
            UPDATE textes_versions
               SET texte_id = %s
             WHERE texte_id IN (%s);
        """ % (uid, row[2]))
        total += len(ids)
        factorized += 1
    print('factorized %i duplicates into %i uniques based on %s' % (total, factorized, key))


def main():
    connect_by_nature_num()

    db.run("""
        INSERT INTO textes (nature, num)
             SELECT nature, num
               FROM textes_versions
              WHERE texte_id IS NULL
                AND nature IS NOT NULL
                AND nature <> 'DECISION'
                AND num IS NOT NULL
           GROUP BY nature, num;
    """)
    print('inserted %i rows in textes based on (nature, num)' % db.changes())

    connect_by_nature_num()
    connect_by_nor()
    connect_by_titrefull_s()

    db.run("""
        INSERT INTO textes (nature, nor)
            SELECT nature, nor
              FROM textes_versions
             WHERE texte_id IS NULL
               AND nor IS NOT NULL
          GROUP BY nor
            HAVING min(nature) = max(nature)
               AND min(titrefull_s) = max(titrefull_s);
    """)
    print('inserted %i rows in textes based on nor' % db.changes())

    db.run("""
        UPDATE textes_versions
           SET texte_id = (
                   SELECT id
                     FROM textes t
                    WHERE t.nor = textes_versions.nor
               )
         WHERE texte_id IS NULL
           AND EXISTS (
                   SELECT id
                     FROM textes t
                    WHERE t.nor = textes_versions.nor
               );
    """)
    print('connected %i rows of textes_versions based on nor' % db.changes())

    factorize_by('titrefull_s')
    connect_by_titrefull_s()

    db.run("""
        INSERT INTO textes (nature, titrefull_s)
            SELECT nature, titrefull_s
              FROM textes_versions
             WHERE texte_id IS NULL
          GROUP BY titrefull_s;
    """)
    print('inserted %i rows in textes based on titrefull_s' % db.changes())

    db.run("""
        UPDATE textes_versions
           SET texte_id = (
                   SELECT id
                     FROM textes t
                    WHERE t.titrefull_s = textes_versions.titrefull_s
               )
         WHERE texte_id IS NULL
           AND EXISTS (
                   SELECT id
                     FROM textes t
                    WHERE t.titrefull_s = textes_versions.titrefull_s
               );
    """)
    print('connected %i rows of textes_versions based on titrefull_s' % db.changes())

    factorize_by('cid')

    xml = etree.XMLParser(remove_blank_text=True)
    q = db.all("""
        SELECT s.id, s.versions, v.texte_id
          FROM textes_structs s
          JOIN textes_versions v ON v.id = s.id
    """)
    for version_id, versions, texte_id in q:
        xml.feed('<VERSIONS>')
        xml.feed(versions)
        xml.feed('</VERSIONS>')
        root = xml.close()
        for lien in root.findall('.//LIEN_TXT'):
            dup_texte_id = db.one("""
                SELECT texte_id FROM textes_versions WHERE id = ? AND texte_id <> ?
            """, (lien.get('id'), texte_id))
            if dup_texte_id:
                print("Erreur: selon les métadonnées de", version_id, "les textes",
                      texte_id, "et", dup_texte_id, "ne devraient être qu'un")

    # Clean up factorized texts
    db.run("""
        DELETE FROM textes
         WHERE NOT EXISTS (
                   SELECT *
                     FROM textes_versions
                    WHERE texte_id = textes.id
               )
    """)
    print('deleted %i unused rows from textes' % db.changes())

    left = db.one("SELECT count(*) FROM textes_versions WHERE texte_id IS NULL")
    if left != 0:
        print("Fail: %i rows haven't been connected" % left)
    else:
        # SQLite doesn't implement DROP COLUMN so we just nullify them instead
        db.run("UPDATE textes SET nor = NULL, titrefull_s = NULL")
        print("done")

    n = db.one("SELECT count(*) FROM textes")
    print("Il y a désormais %i textes dans la base." % n)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('--from-scratch')
    args = p.parse_args()

    db = connect_db(args.db)
    try:
        with db:
            if args.from_scratch:
                db.executescript("""
                    DELETE FROM textes;
                    UPDATE textes_versions SET texte_id = NULL WHERE texte_id IS NOT NULL;
                """)
            if db.one("SELECT id FROM textes_versions WHERE titrefull_s IS NULL LIMIT 1"):
                print("> Normalisation des titres...")
                normalize(db)
                print("> Factorisation des textes...")
            main()
    except KeyboardInterrupt:
        pass
