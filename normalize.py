# encoding: utf8

"""
Normalizes LEGI data stored in an SQLite DB
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from datetime import date
import re
from sqlite3 import OperationalError

from fr_calendar import (
    MOIS_REPU, MOIS_REPU_MAP, gregorian_to_republican, republican_to_gregorian
)
from roman import decimal_to_roman
from utils import connect_db, filter_nonalnum, input, strip_down, strip_prefix


AUTORITE_MAP = {
    "CONSEIL D'ETAT": "du Conseil d'État",
    "ROI": "du Roi",
}
MOIS_GREG = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
MOIS_GREG_MAP = {strip_down(m): i for i, m in enumerate(MOIS_GREG, 1)}
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
nonword_re = re.compile(r'\W', re.U)
numero_re = re.compile(r'n°(?!\s)', re.U)
premier_du_mois = re.compile(r'\b1 %(mois_p)s %(annee_p)s' % globals())
spaces_re = re.compile(r'\s+', re.U)
word_re = re.compile(r'\w{2,}', re.U)

ordure_p = r'quinquennale?'
annexe_p = r"(?P<annexe>Annexe (au |à la |à l'|du ))"
autorite_p = r'(?P<autorite>ministériel(le)?|du Roi|du Conseil d\'[EÉ]tat)'
date_p = r'(du )?(%(jour_p)s )?%(mois_p)s( %(annee_p)s)?( (?P=annee))?' % globals()
nature_p = r'(?P<nature>Arrêté|Code|Constitution|Convention|Décision|Déclaration|Décret(-loi)?|Loi( constitutionnelle| organique)?|Ordonnance)'
numero_p = r'(n° ?)?(?P<numero>[0-9]+([\-–][0-9]+)*(, ?[0-9]+(-[0-9]+)*)*( et autres)?)\.?'
titre1_re = re.compile(r'(%(annexe_p)s)?%(nature_p)s' % globals(), re.U | re.I)
titre2_re = re.compile(r'( %(autorite_p)s| %(date_p)s| %(numero_p)s| %(ordure_p)s)' % globals(), re.U | re.I)


def gen_titre(annexe, nature, num, date_texte, calendar, autorite):
    if not nature:
        return ''
    if annexe:
        titre = annexe[0].upper() + annexe[1:].lower()
        titre += NATURE_MAP.get(nature, nature).lower()
    else:
        titre = NATURE_MAP.get(nature, nature.title())
    if autorite:
        titre += ' ' + AUTORITE_MAP[autorite]
    if num:
        titre += ' n° '+num
    if date_texte and date_texte != '2999-01-01':
        year, month, day = map(int, date_texte.split('-'))
        if calendar == 'republican':
            year, month, day = gregorian_to_republican(year, month, day)
            titre += ' du %s' % day
            if month:
                titre += ' ' + month
            titre += ' an ' + decimal_to_roman(year)
        else:
            assert calendar == 'gregorian'
            titre += ' du %s %s %s' % (day, MOIS_GREG[month-1], year)
        titre = titre.replace(' 1 ', ' 1er ')
    return titre


def normalize_title(title):
    if not title:
        return title
    title = spaces_re.sub(' ', title.strip())
    title = title.rstrip('.').rstrip()
    title = numero_re.sub('n° ', title)
    title = premier_du_mois.sub(r'1er \1 \2', title)
    if title[0].islower():
        title = title[0].upper() + title[1:]
    else:
        first_space = title.find(' ')
        first_word = title[:first_space]
        if first_word.isupper():
            first_word = first_word.title()
            title = first_word + title[first_space:]
        if first_word[-1] == 's':
            title = first_word[:-1] + title[first_space:]
    title = title.replace('constitutionel', 'constitutionnel')
    return title


def parse_titre(anomaly, titre):
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
        for k, v in m.groupdict().items():
            if v is None or k in duplicates:
                continue
            if k == 'numero':
                v = v.replace('–', '-')
            elif k == 'jour':
                v = v.lower().replace('1er', '1')
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
            print('Incohérence: ', k, ': "', d[k], '" ≠ "', v, '"\n'
                  '       dans: "', titre, '"', sep='')
            anomaly[0] = True
            duplicates.add(k)
            d.pop(k)


def upper_words_percentage(s):
    words = word_re.findall(s)
    return len([w for w in words if w.isupper()]) / len(words)


def main(db):

    db.executescript("""
        UPDATE textes_versions SET date_texte = NULL WHERE nor IS NOT NULL AND date_texte < '1868-01-01';
        UPDATE textes_versions SET num = substr(num, 1, length(num)-1) WHERE num like '%.';
        UPDATE textes_versions SET num = NULL WHERE num = date_texte;
        UPDATE textes_versions SET num_sequence = NULL WHERE num_sequence = 0;
        UPDATE textes_versions SET page_deb_publi = NULL WHERE page_deb_publi = 0;
        UPDATE textes_versions SET page_fin_publi = NULL WHERE page_fin_publi = 0;
    """)

    try:
        db.executescript("""
            ALTER TABLE textes_versions ADD COLUMN titrefull_s text;
            CREATE INDEX textes_versions_titrefull_s ON textes_versions (titrefull_s);
        """)
    except OperationalError:
        pass

    sql = db.execute

    q = db.all("""
        SELECT rowid, titre, titrefull, titrefull_s, nature, num, date_texte, autorite
          FROM textes_versions
    """)
    for row in q:
        rowid, titre_o, titrefull_o, titrefull_s_o, nature_o, num, date_texte, autorite = row
        titre, titrefull, nature = titre_o, titrefull_o, nature_o
        if titrefull.startswith('COUR DES COMPTESET DE FINANCEMENTS POLITIQUES '):
            titrefull = titrefull[46:]
        len_titre = len(titre)
        if len(titrefull) > len_titre:
            if titrefull[len_titre:][:1] != ' ' and titrefull[:len_titre] == titre:
                # Add missing space
                titrefull = titre + ' ' + titrefull[len_titre:]
        titre, titrefull = normalize_title(titre), normalize_title(titrefull)
        if titre.endswith(' du'):
            titre = titre[:-3]
        len_titre = len(titre)
        if titrefull[:len_titre] != titre:
            if len_titre > len(titrefull):
                titrefull = titre
            elif nonword_re.sub('', titrefull) == nonword_re.sub('', titre):
                titre = titrefull
                len_titre = len(titre)
            elif strip_down(titre) == strip_down(titrefull[:len_titre]):
                has_upper_1 = upper_words_percentage(titre) > 0
                has_upper_2 = upper_words_percentage(titrefull[:len_titre]) > 0
                if has_upper_1 ^ has_upper_2:
                    if has_upper_1:
                        titre = titrefull[:len_titre]
                    else:
                        titrefull = titre + titrefull[len_titre:]
                elif not (has_upper_1 or has_upper_2):
                    n_upper_1 = len([c for c in titre if c.isupper()])
                    n_upper_2 = len([c for c in titrefull if c.isupper()])
                    if n_upper_1 > n_upper_2:
                        titrefull = titre + titrefull[len_titre:]
                    elif n_upper_2 > n_upper_1:
                        titre = titrefull[:len_titre]
        if upper_words_percentage(titre) > 0.2:
            print('Échec: titre "', titre, '" contient beaucoup de mots en majuscule', sep='')
        if nature != 'CODE':
            anomaly = [False]
            d1, endpos1 = parse_titre(anomaly, titre)
            if not d1 and titre != 'Annexe' or d1 and endpos1 < len_titre:
                print('Fail: regex did not fully match titre "', titre, '"', sep='')
            d2, endpos2 = parse_titre(anomaly, titrefull)
            if not d2:
                print('Fail: regex did not match titrefull "', titrefull, '"', sep='')
            if d1 or d2:
                def get_key(key, ignore_not_found=False):
                    g1, g2 = d1.get(key), d2.get(key)
                    if not (g1 or g2) and not ignore_not_found:
                        print('Échec: ', key, ' trouvé ni dans "', titre, '" (titre) ni dans "', titrefull, '" (titrefull)', sep='')
                        anomaly[0] = True
                        return
                    if g1 is None or g2 is None:
                        return g1 if g2 is None else g2
                    if strip_down(g1) == strip_down(g2):
                        return g1
                    if key == 'nature' and g1.split()[0] == g2.split()[0]:
                        return g1 if len(g1) > len(g2) else g2
                    print('Incohérence: ', key,  ': "', g1, '" ≠ "', g2, '"\n',
                          '      titre: "', titre, '"\n',
                          '  titrefull: "', titrefull, '"',
                          sep='')
                    anomaly[0] = True
                annexe = get_key('annexe', ignore_not_found=True)
                nature_d = get_key('nature').upper()
                nature_d = NATURE_MAP_R.get(nature_d, nature_d)
                if nature_d and nature_d != nature:
                    if not nature:
                        nature = nature_d
                    elif nature_d.split('_')[0] == nature.split('_')[0]:
                        if len(nature_d) > len(nature):
                            nature = nature_d
                    else:
                        print('Incohérence: nature: "', nature_d, '" (detectée) ≠ "', nature, '" (donnée)', sep='')
                        anomaly[0] = True
                num_d = get_key('numero', ignore_not_found=True)
                if num_d and num_d != num and num_d != date_texte:
                    if not num or not num[0].isdigit():
                        if not annexe:  # On ne veut pas donner le numéro d'un décret à son annexe
                            if '-' in num_d:
                                num = num_d
                                sql("UPDATE textes_versions SET num = ? WHERE rowid = ?",
                                    (num, rowid))
                    else:
                        print('Incohérence: numéro: "', num_d, '" (detecté) ≠ "', num, '" (donné)', sep='')
                        anomaly[0] = True
                calendar = 'gregorian'
                jour = get_key('jour')
                mois = get_key('mois')
                annee = get_key('annee')
                if jour and mois and annee:
                    jour = int(jour.lower().replace('1er', '1'))
                    if mois in MOIS_REPU_MAP:
                        calendar = 'republican'
                        annee = strip_prefix(annee, 'an ')
                        d = republican_to_gregorian(annee, mois, jour)
                    else:
                        mois = MOIS_GREG_MAP[strip_down(mois)]
                        d = date(int(annee), mois, jour)
                    date_texte_d = d.isoformat()
                    if not date_texte or date_texte == '2999-01-01':
                        date_texte = date_texte_d
                        sql("UPDATE textes_versions SET date_texte = ? WHERE rowid = ?",
                            (date_texte, rowid))
                    elif date_texte_d != date_texte:
                        print('Incohérence: date: "', date_texte_d, '" (detectée) ≠ "', date_texte, '" (donnée)', sep='')
                        anomaly[0] = True
                autorite_d = get_key('autorite', ignore_not_found=True)
                if autorite_d:
                    autorite_d = strip_down(autorite_d)
                    if not autorite_d.startswith('ministeriel'):
                        autorite_d = strip_prefix(autorite_d, 'du ').upper()
                        if not autorite:
                            autorite = autorite_d
                            sql("UPDATE textes_versions SET autorite = ? WHERE rowid = ?",
                                (autorite, rowid))
                        elif autorite != autorite_d:
                            print('Incohérence: autorité "', autorite_d, '" (detectée) ≠ "', autorite, '" (donnée)', sep='')
                            anomaly[0] = True
                if not anomaly[0]:
                    titre = gen_titre(annexe, nature, num, date_texte, calendar, autorite)
                    len_titre = len(titre)
                    titrefull = titre + titrefull[endpos2:]
        if titre != titre_o or titrefull != titrefull_o or nature != nature_o:
            sql("""
                UPDATE textes_versions
                   SET titre = ?
                     , titrefull = ?
                     , nature = ?
                 WHERE rowid = ?
            """, (titre, titrefull, nature, rowid))
        titrefull_s = filter_nonalnum(titrefull)
        if titrefull_s != titrefull_s_o:
            sql("""
                UPDATE textes_versions
                   SET titrefull_s = ?
                 WHERE rowid = ?
            """, (titrefull_s, rowid))


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    args = p.parse_args()

    db = connect_db(args.db)
    try:
        with db:
            main(db)
            save = input('Sauvegarder les modifications? (o/n) ')
            if save.lower() != 'o':
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
