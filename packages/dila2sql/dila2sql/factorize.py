from argparse import ArgumentParser

from lxml import etree

from .normalize import normalize_text_titles
from .utils import connect_db
from .models import db_proxy, Texte, TexteVersion


def connect_by_nature_num(db):
    cursor = db.execute_sql("""
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
    db.commit()
    print('connected %i rows of textes_versions based on (nature, num)' % cursor.rowcount)


def connect_by_nor(db):
    db.execute_sql("""
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
    db.commit()
    db.execute_sql("CREATE UNIQUE INDEX texte_by_nor_index ON texte_by_nor (nor)")
    db.commit()
    cursor = db.execute_sql("""
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
    db.commit()
    print('connected %i rows of textes_versions based on nor' % cursor.rowcount)
    db.execute_sql("DROP TABLE texte_by_nor")
    db.commit()


def connect_by_titrefull_s(db):
    db.execute_sql("""
        CREATE TEMP TABLE texte_by_titrefull_s AS
            SELECT DISTINCT titrefull_s, texte_id
              FROM textes_versions
             WHERE texte_id IS NOT NULL;
    """)
    db.commit()
    db.execute_sql("CREATE UNIQUE INDEX texte_by_titrefull_s_index ON texte_by_titrefull_s (titrefull_s)")
    db.commit()
    cursor = db.execute_sql("""
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
    db.commit()
    print('connected %i rows of textes_versions based on titrefull_s' % cursor.rowcount)
    db.execute_sql("DROP TABLE texte_by_titrefull_s")
    db.commit()


def factorize_by(db, key):
    duplicates = db.execute_sql("""
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
        uid = Texte.select(Texte.id).order_by(Texte.id.desc()).first().id + 1
        if key == 'cid':
            Texte.insert(id=uid, nature=row[0]).execute()
        else:
            Texte.insert(id=uid, nature=row[0], **{key: row[1]}).execute()
        TexteVersion.update(texte_id=uid) \
            .where(TexteVersion.texte_id.in_(ids)).execute()
        total += len(ids)
        factorized += 1
    print('factorized %i duplicates into %i uniques based on %s' % (total, factorized, key))


def main(db):
    print("> Factorisation des textes...")

    connect_by_nature_num(db)

    cursor = db.execute_sql("""
        INSERT INTO textes (nature, num)
             SELECT nature, num
               FROM textes_versions
              WHERE texte_id IS NULL
                AND nature IS NOT NULL
                AND nature <> 'DECISION'
                AND num IS NOT NULL
           GROUP BY nature, num;
    """)
    db.commit()
    print('inserted %i rows in textes based on (nature, num)' % cursor.rowcount)

    connect_by_nature_num(db)
    connect_by_nor(db)
    connect_by_titrefull_s(db)

    cursor = db.execute_sql("""
        INSERT INTO textes (nature, nor)
            SELECT nature, nor
              FROM textes_versions
             WHERE texte_id IS NULL
               AND nor IS NOT NULL
          GROUP BY nor
            HAVING min(nature) = max(nature)
               AND min(titrefull_s) = max(titrefull_s);
    """)
    db.commit()
    print('inserted %i rows in textes based on nor' % cursor.rowcount)

    cursor = db.execute_sql("""
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
    db.commit()
    print('connected %i rows of textes_versions based on nor' % cursor.rowcount)

    factorize_by(db, 'titrefull_s')
    connect_by_titrefull_s(db)

    cursor = db.execute_sql("""
        INSERT INTO textes (nature, titrefull_s)
            SELECT nature, titrefull_s
              FROM textes_versions
             WHERE texte_id IS NULL
          GROUP BY titrefull_s;
    """)
    db.commit()
    print('inserted %i rows in textes based on titrefull_s' % cursor.rowcount)

    cursor = db.execute_sql("""
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
    db.commit()
    print('connected %i rows of textes_versions based on titrefull_s' % cursor.rowcount)

    factorize_by(db, 'cid')

    xml = etree.XMLParser(remove_blank_text=True)
    q = db.execute_sql("""
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
            texte_version = TexteVersion.select(texte_id) \
                .where(TexteVersion.id == lien.get('id') & TexteVersion.texte_id != texte_id) \
                .first()
            dup_texte_id = texte_version.texte_id if texte_version else None
            if dup_texte_id:
                print("Erreur: selon les métadonnées de", version_id, "les textes",
                      texte_id, "et", dup_texte_id, "ne devraient être qu'un")

    # Clean up factorized texts
    cursor = db.execute_sql("""
        DELETE FROM textes
         WHERE NOT EXISTS (
                   SELECT *
                     FROM textes_versions
                    WHERE texte_id = textes.id
               )
    """)
    db.commit()
    print('deleted %i unused rows from textes' % cursor.rowcount)

    left = TexteVersion.select().where(TexteVersion.texte_id.is_null()).count()
    if left != 0:
        print("Fail: %i rows haven't been connected" % left)
    else:
        # SQLite doesn't implement DROP COLUMN so we just nullify them instead
        db.execute_sql("UPDATE textes SET nor = NULL, titrefull_s = NULL")
        db.commit()
        print("done")

    n = Texte.select().count()
    print("Il y a désormais %i textes dans la base." % n)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('--from-scratch')
    args = p.parse_args()

    db = connect_db(args.db)
    db_proxy.initialize(db)
    with db:
        if args.from_scratch:
            db.execute_sql("DELETE FROM textes;")
            db.commit()
            db.execute_sql("""
              UPDATE textes_versions SET texte_id = NULL WHERE texte_id IS NOT NULL;
            """)
            db.commit()
        missing_titre = TexteVersion \
            .select(TexteVersion.id) \
            .where(TexteVersion.titrefull_s.is_null()) \
            .first()
        if missing_titre:
            normalize_text_titles(db)
        main(db)
