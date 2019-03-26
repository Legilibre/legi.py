import json
from collections import defaultdict
from .utils import get_table
from dila2sql.models import DuplicateFile, ArticleCalipso, TexteVersionBrute, \
    Conteneur, Lien, Sommaire, TABLE_TO_MODEL


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
