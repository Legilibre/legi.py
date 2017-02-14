# encoding: utf8

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from datetime import date, timedelta
import sys

from .titles import NATURE_MAP_R, parse_titre, spaces_re
from .utils import connect_db, reconstruct_path, strip_down


def anomalies_date_fin_etat(db, err):
    a = [('articles', 'article'), ('textes_versions', 'texte/version')]
    last_update = db.one("SELECT value FROM db_meta WHERE key = 'last_update'")
    day, heure = last_update.split('-')
    assert len(day) == 8
    annee, mois, jour = day[:4], day[4:6], day[6:]
    current_day = annee + '-' + mois + '-' + jour
    near_future = date(int(annee), int(mois), int(jour)) + timedelta(days=5)
    near_future = near_future.isoformat()
    for table, sous_dossier in a:
        q = db.all("""
            SELECT dossier, cid, id, date_fin, etat
              FROM {0}
             WHERE date_fin <> '2999-01-01'
               AND ( etat LIKE 'VIGUEUR%' AND date_fin < '{1}' OR
                     etat NOT LIKE 'VIGUEUR%' AND etat <> 'ABROGE_DIFF' AND date_fin > '{2}'
                   )
        """.format(table, current_day, near_future))
        for row in q:
            dossier, cid, id, date_fin, etat = row
            path = reconstruct_path(dossier, cid, sous_dossier, id)
            x = 'passé' if etat.startswith('VIGUEUR') else 'futur'
            err(path, 'la date de fin "', date_fin, '" est dans le ', x, ' mais l\'état est "', etat, '"')


def anomalies_orphans(db, err):
    db.run("CREATE INDEX IF NOT EXISTS sommaires_element_idx ON sommaires (element)")
    q = db.all("""
        SELECT dossier, cid, id
          FROM articles a
         WHERE (SELECT count(*) FROM sommaires so WHERE so.element = a.id) = 0
    """)
    for dossier, cid, id in q:
        path = reconstruct_path(dossier, cid, 'article', id)
        err(path, "article orphelin, il n'apparaît dans aucun texte")
    q = db.all("""
        SELECT dossier, cid, id
          FROM sections s
         WHERE (SELECT count(*) FROM sommaires so WHERE so.element = s.id) = 0
    """)
    for dossier, cid, id in q:
        path = reconstruct_path(dossier, cid, 'section_ta', id)
        err(path, "section orpheline, elle n'apparaît dans aucun texte")
    db.run("DROP INDEX sommaires_element_idx")


def anomalies_sections(db, err):
    q = db.all("""
        SELECT s.dossier, s.cid, s.id, num, debut, etat, count(*) as count
          FROM sommaires so
          JOIN sections s ON s.id = so.parent
         WHERE etat NOT LIKE 'MODIF%'
           AND lower(num) NOT LIKE 'annexe%'
      GROUP BY s.id, num, debut, etat
        HAVING count(*) > 1
    """)
    for row in q:
        dossier, cid, section, num, debut, etat, count = row
        path = reconstruct_path(dossier, cid, 'section_ta', section)
        err(path, count, ' articles avec le numéro "', num,
            '", la date de début "', debut,
            '" et l\'état "', etat, '"')

    q = db.all("""
        SELECT DISTINCT s.dossier, s.cid, s.id, a.dossier, a.cid, a.id, so.etat, a.etat
          FROM sommaires so
          JOIN articles a ON a.id = so.element AND a.etat <> so.etat
          JOIN sections s ON s.id = so.parent
    """)
    for row in q:
        dossier, cid, id, a_dossier, a_cid, a_id, sa_etat, a_etat = row
        path = reconstruct_path(dossier, cid, 'section_ta', id)
        a_path = reconstruct_path(a_dossier, a_cid, 'article', a_id)
        err(path, 'l\'état "', sa_etat, '" ne correspond pas à l\'état "', a_etat,
            '" dans le fichier ', a_path)


def anomalies_textes_versions(db, err):
    def normalize_title(path, col, title):
        if not title:
            return title
        title = spaces_re.sub(' ', title.strip())
        if 'constitutionel' in title:
            err(path, 'faute d\'orthographe dans le ', col, ': "constitutionel"')
            title = title.replace('constitutionel', 'constitutionnel')
        return title

    q = db.all("""
        SELECT dossier, cid, id, titre, titrefull, nature, num, date_texte
          FROM textes_versions_brutes_view
    """)
    for row in q:
        dossier, cid, id, titre_o, titrefull_o, nature_o, num, date_texte = row
        path = reconstruct_path(dossier, cid, 'texte/version', id)

        num = num or ''
        if num and num[-1] == '.':
            err(path, 'num "', num, '" se termine par un point')
            num = num[:-1]

        titre, titrefull, nature = titre_o, titrefull_o, nature_o
        len_titre = len(titre)
        if len(titrefull) > len_titre:
            if titrefull[len_titre] != ' ' and titrefull[:len_titre] == titre:
                err(path, 'espace manquante dans titrefull après le ', len_titre, 'e caractère')
                titrefull = titre + ' ' + titrefull[len_titre:]
        titre = normalize_title(path, 'titre', titre)
        titrefull = normalize_title(path, 'titrefull', titrefull)
        if titre.endswith(' du'):
            err(path, 'titre finit par "du"')
            titre = titre[:-3]
        len_titre = len(titre)
        if len_titre > len(titrefull):
            err(path, 'titre est plus long que titrefull')
            titrefull = titre
        if nature != 'CODE':
            def anomaly_cb(col):
                def f(titre, k, v1, v2):
                    err(path, k, ': "', v1, '" ≠ "', v2, '" dans ', col)
                return f
            d1, endpos1 = parse_titre(titre, anomaly_cb('titre'), strict=True)
            if not d1 and titre != 'Annexe' or d1 and endpos1 < len_titre:
                err(path, 'titre est irrégulier: "', titre, '"')
            d2, endpos2 = parse_titre(titrefull, anomaly_cb('titrefull'), strict=True)
            if not d2:
                err(path, 'titrefull est irrégulier: "', titrefull, '"')
            if d2:
                titrefull_p2 = titrefull[endpos2:]
                if titrefull_p2 and titrefull_p2[0] != ' ':
                    err(path, 'espace manquante dans titrefull après le ', endpos2, 'e caractère')
            if d1 or d2:
                def get_key(key, ignore_not_found=False):
                    g1, g2 = d1.get(key), d2.get(key)
                    if not (g1 or g2) and not ignore_not_found:
                        err(path, key, ' trouvé ni dans "', titre, '" (titre) ni dans "', titrefull, '" (titrefull)')
                        return
                    if g1 is None or g2 is None:
                        return g1 if g2 is None else g2
                    if strip_down(g1) == strip_down(g2):
                        return g1
                    if key == 'nature' and g1.split()[0] == g2.split()[0]:
                        return g1 if len(g1) > len(g2) else g2
                    err(path, key, ': "', g1, '" (dans titre) ≠ "', g2, '" (dans titrefull)')
                annexe = get_key('annexe', ignore_not_found=True)
                nature = get_key('nature').upper()
                nature = NATURE_MAP_R.get(nature, nature)
                if nature_o and nature != nature_o:
                    err(path, 'nature: "', nature, '" (detectée) ≠ "', nature_o, '" (donnée)')
                    if nature.split('_')[0] == nature_o.split('_')[0]:
                        if len(nature_o) > len(nature):
                            nature = nature_o
                num_d = get_key('numero', ignore_not_found=True)
                if annexe:  # On ne veut pas donner le numéro d'un décret à son annexe
                    num_d = None
                if num_d and '-' not in num_d:
                    num_d = None
                if num_d and num_d != num:
                    err(path, 'numéro: "', num_d, '" (detecté) ≠ "', num, '" (donné)')
                    if not num:
                        num = num_d
                if num and num == date_texte:
                    err(path, 'num est égal à date_texte: "', num, '"')
                    num = ''
                date_texte_d = get_key('date')
                if date_texte_d and date_texte_d != date_texte:
                    err(path, 'date: "', date_texte_d, '" (detectée) ≠ "', date_texte, '" (donnée)')
                get_key('calendar')


def detect_anomalies(db, out=sys.stdout):
    count = [0]
    def err(path, *a):
        print(path, ': ', *a, sep='', file=out)
        out.flush()
        count[0] += 1

    anomalies_date_fin_etat(db, err)
    anomalies_orphans(db, err)
    anomalies_sections(db, err)
    anomalies_textes_versions(db, err)
    return count[0]


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    args = p.parse_args()
    detect_anomalies(connect_db(args.db))
