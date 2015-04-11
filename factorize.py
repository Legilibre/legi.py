# encoding: utf8
from __future__ import print_function, unicode_literals

from argparse import ArgumentParser
from sqlite3 import connect, OperationalError

from utils import input, inserter, iter_results


def connect_by_nature_num():
    conn.executescript("""
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
    print('connected %i rows of textes_versions based on (nature, num)' % changes())

def connect_by_nor():
    conn.executescript("""
        CREATE TEMP TABLE texte_by_nor AS
            SELECT nor, min(texte_id)
              FROM textes_versions
             WHERE nor IS NOT NULL
               AND texte_id IS NOT NULL
          GROUP BY nor
            HAVING min(nature) = max(nature)
               AND min(num) = max(num)
               AND min(texte_id) = max(texte_id);
        CREATE UNIQUE INDEX texte_by_nor_index ON texte_by_nor (nor);

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
    print('connected %i rows of textes_versions based on nor' % changes())
    conn.executescript("DROP TABLE texte_by_nor")

def connect_by_cid_id():
    conn.executescript("""
        CREATE TEMP TABLE texte_by_cid_id AS
            SELECT DISTINCT cid, id, texte_id
              FROM textes_versions
             WHERE texte_id IS NOT NULL;
        CREATE UNIQUE INDEX texte_by_cid_id_index ON texte_by_cid_id (cid, id);

        UPDATE textes_versions
           SET texte_id = (
                   SELECT texte_id
                     FROM texte_by_cid_id t
                    WHERE t.cid = textes_versions.cid
                      AND t.id = textes_versions.id
               )
         WHERE texte_id IS NULL
           AND EXISTS (
                   SELECT texte_id
                     FROM texte_by_cid_id t
                    WHERE t.cid = textes_versions.cid
                      AND t.id = textes_versions.id
               );
    """)
    print('connected %i rows of textes_versions based on (cid, id)' % changes())
    conn.executescript("DROP TABLE texte_by_cid_id")

def connect_by_titrefull_s():
    conn.executescript("""
        CREATE TEMP TABLE texte_by_titrefull_s AS
            SELECT DISTINCT titrefull_s, texte_id
              FROM textes_versions
             WHERE texte_id IS NOT NULL;
        CREATE UNIQUE INDEX texte_by_titrefull_s_index ON texte_by_titrefull_s (titrefull_s);

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
    print('connected %i rows of textes_versions based on titrefull_s' % changes())
    conn.executescript("DROP TABLE texte_by_titrefull_s")


def factorize_by(key):
    col = key.replace('||', '_')
    duplicates = sql("""
        SELECT min(nature), {0}, group_concat(texte_id)
          FROM textes_versions
         WHERE texte_id IS NOT NULL
      GROUP BY {0}
        HAVING min(texte_id) <> max(texte_id)
           AND min(nature) = max(nature)
    """.format(key))
    total = 0
    factorized = 0
    for row in iter_results(duplicates):
        ids = tuple(row[2].split(','))
        sql("INSERT INTO textes (nature, {0}) VALUES (?, ?)".format(col),
            (row[0], row[1]))
        uid = one("SELECT id FROM textes WHERE {0} = ?".format(col), (row[1],))
        sql("""
            UPDATE textes_versions
               SET texte_id = %s
             WHERE texte_id IN (%s);
        """ % (uid, row[2]))
        total += len(ids)
        factorized += 1
    print('factorized %i duplicates into %i uniques based on %s' % (total, factorized, key))


def main():
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS textes
        ( id integer primary key
        , nature text
        , num text
        , nor char(12) unique -- only used during factorization
        , titrefull_s text unique -- only used during factorization
        , cid_id text unique -- only used during factorization
        , UNIQUE (nature, num)
        );
    """)
    try:
        conn.executescript("""
            ALTER TABLE textes_versions ADD COLUMN texte_id integer REFERENCES textes;
            CREATE INDEX textes_versions_texte_id ON textes_versions (texte_id);
        """)
    except OperationalError:
        pass

    connect_by_nature_num()

    conn.executescript("""
        INSERT INTO textes (nature, num)
             SELECT nature, num
               FROM textes_versions
              WHERE texte_id IS NULL
                AND nature IS NOT NULL
                AND num IS NOT NULL
           GROUP BY nature, num;
    """)
    print('inserted %i rows in textes based on (nature, num)' % changes())

    connect_by_nature_num()
    connect_by_nor()
    connect_by_cid_id()
    connect_by_titrefull_s()

    conn.executescript("""
        INSERT INTO textes (nature, nor)
            SELECT nature, nor
              FROM textes_versions
             WHERE texte_id IS NULL
               AND nor IS NOT NULL
          GROUP BY nor
            HAVING min(nature) = max(nature)
               AND min(titrefull_s) = max(titrefull_s);
    """)
    print('inserted %i rows in textes based on nor' % changes())

    conn.executescript("""
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
    print('connected %i rows of textes_versions based on nor' % changes())

    factorize_by('titrefull_s')
    connect_by_cid_id()
    connect_by_titrefull_s()

    conn.executescript("""
        INSERT INTO textes (nature, titrefull_s)
            SELECT nature, titrefull_s
              FROM textes_versions
             WHERE texte_id IS NULL
          GROUP BY titrefull_s;
    """)
    print('inserted %i rows in textes based on titrefull_s' % changes())

    conn.executescript("""
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
    print('connected %i rows of textes_versions based on titrefull_s' % changes())

    factorize_by('cid||id')

    # Clean up factorized texts
    sql("""
        DELETE FROM textes
         WHERE NOT EXISTS (
                   SELECT *
                     FROM textes_versions
                    WHERE texte_id = textes.id
               )
    """)
    print('deleted %i unused rows from textes' % changes())

    left = one("SELECT count(*) FROM textes_versions WHERE texte_id IS NULL")
    if left != 0:
        print("Fail: %i rows haven't been connected")
    else:
        # SQLite doesn't implement DROP COLUMN so we just nullify them instead
        sql("UPDATE textes SET nor = NULL, titrefull_s = NULL, cid_id = NULL")
        print("done")


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    args = p.parse_args()

    conn = connect(args.db)

    sql = conn.execute
    insert = inserter(conn)

    def one(*args):
        r = conn.execute(*args).fetchone()
        if len(r) == 1:
            return r[0]
        return r

    changes = lambda: one("SELECT changes()")

    try:
        with conn:
            main()
            save = input('Sauvegarder les modifications? (o/n) ')
            if save.lower() != 'o':
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
