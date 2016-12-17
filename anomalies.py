# encoding: utf8

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from datetime import date
import re
import sys

from fr_calendar import MOIS_GREG, MOIS_REPU, convert_date_to_iso
from utils import connect_db, reconstruct_path, strip_down


NATURE_MAP = {
    "ARRETE": "Arrêté",
    "DECISION": "Décision",
    "DECLARATION": "Déclaration",
    "DECRET": "Décret",
    "DECRET_LOI": "Décret-loi",
    "LOI_CONSTIT": "Loi constitutionnelle",
    "LOI_ORGANIQUE": "Loi organique",
}
NATURE_MAP_R = {v.upper(): k for k, v in NATURE_MAP.items()}


jour_p = r'(?P<jour>1er|[0-9]{1,2})'
mois_p = r'(?P<mois>%s)' % '|'.join(MOIS_GREG+MOIS_REPU)
annee_p = r'(?P<annee>[0-9]{4,}|an [IVX]+)'
numero_re = re.compile(r'n°(?!\s)', re.U)
spaces_re = re.compile(r'\s+', re.U)
word_re = re.compile(r'\w{2,}', re.U)

ordure_p = r'quinquennale?'
annexe_p = r"(?P<annexe>Annexe (au |à la |à l'|du ))"
autorite_p = r'(?P<autorite>ministériel(le)?|du Roi|du Conseil d\'[EÉ]tat)'
date_p = r'(du )?(?P<date>(%(jour_p)s )?%(mois_p)s( %(annee_p)s)?)( (?P=annee))?' % globals()
nature_p = r'(?P<nature>Arrêté|Code|Constitution|Convention|Décision|Déclaration|Décret(-loi)?|Loi( constitutionnelle| organique)?|Ordonnance)'
numero_p = r'(n° ?)?(?P<numero>[0-9]+([\-–][0-9]+)*(, ?[0-9]+(-[0-9]+)*)*( et autres)?)\.?'
titre1_re = re.compile(r'(%(annexe_p)s)?%(nature_p)s' % globals(), re.U | re.I)
titre2_re = re.compile(r'( %(autorite_p)s| \(?%(date_p)s\)?| %(numero_p)s| %(ordure_p)s)' % globals(), re.U | re.I)


def normalize_title(path, col, title):
    if not title:
        return title
    title = spaces_re.sub(' ', title.strip())
    if 'constitutionel' in title:
        err(path, 'faute d\'orthographe dans le ', col, ': "constitutionel"')
        title = title.replace('constitutionel', 'constitutionnel')
    return title


def parse_titre(path, col, titre):
    m = titre1_re.match(titre)
    if not m:
        return {}, 0
    d = m.groupdict()
    duplicates = set()
    while True:
        pos = m.end()
        m = titre2_re.match(titre, pos)
        if not m:
            return d, pos
        groups = m.groupdict()
        if 'date' in groups:
            groups['date'], groups['calendar'] = convert_date_to_iso(
                groups.pop('jour'),
                groups.pop('mois'),
                groups.pop('annee'),
            )
        for k, v in groups.items():
            if v is None or k in duplicates:
                continue
            if k == 'numero':
                v = v.replace('–', '-')
            if k not in d:
                d[k] = v
                continue
            if d[k] == v or strip_down(d[k]) == strip_down(v):
                continue
            if k == 'numero':
                a, b = sorted((d[k], v), key=len)
                x, y = b.split('-', 1)
                if a == x or a == y:
                    d[k] = b
                    continue
            if k == 'calendar':
                continue
            err(path, k, ': "', d[k], '" ≠ "', v, '" dans ', col)
            duplicates.add(k)
            d.pop(k)


def upper_words_percentage(s):
    words = word_re.findall(s)
    return len([w for w in words if w.isupper()]) / len(words)


def err(path, *a):
    print(path, ': ', *a, sep='')
    sys.stdout.flush()


def anomalies_date_fin_etat(db):
    a = [('articles', 'article'), ('textes_versions', 'texte/version')]
    for table, sous_dossier in a:
        q = db.all("""
            SELECT dossier, cid, id, date_fin, etat
              FROM {0}
             WHERE date_fin <> '2999-01-01'
               AND ( etat LIKE 'VIGUEUR%' AND date_fin < '{1}' OR
                     etat NOT LIKE 'VIGUEUR%' AND etat <> 'ABROGE_DIFF' AND date_fin > '{1}'
                   )
        """.format(table, date.today().isoformat()))
        for row in q:
            dossier, cid, id, date_fin, etat = row
            path = reconstruct_path(dossier, cid, sous_dossier, id)
            x = 'passé' if etat.startswith('VIGUEUR') else 'futur'
            err(path, 'la date de fin "', date_fin, '" est dans le ', x, ' mais l\'état est "', etat, '"')


def anomalies_orphans(db):
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


def anomalies_sections(db):
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
    """.format(date.today().isoformat()))
    for row in q:
        dossier, cid, id, a_dossier, a_cid, a_id, sa_etat, a_etat = row
        path = reconstruct_path(dossier, cid, 'section_ta', id)
        a_path = reconstruct_path(a_dossier, a_cid, 'article', a_id)
        err(path, 'l\'état "', sa_etat, '" ne correspond pas à l\'état "', a_etat,
            '" dans le fichier ', a_path)


def anomalies_textes_versions(db):
    q = db.all("""
        SELECT dossier, cid, id, titre, titrefull, nature, num, date_texte
          FROM textes_versions
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
            d1, endpos1 = parse_titre(path, 'titre', titre)
            if not d1 and titre != 'Annexe' or d1 and endpos1 < len_titre:
                err(path, 'titre est irrégulier: "', titre, '"')
            d2, endpos2 = parse_titre(path, 'titrefull', titrefull)
            if not d2:
                err(path, 'titrefull est irrégulier: "', titrefull, '"')
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


def main(db):
    anomalies_date_fin_etat(db)
    anomalies_orphans(db)
    anomalies_sections(db)
    anomalies_textes_versions(db)


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    args = p.parse_args()
    main(connect_db(args.db))
