# encoding: utf8

"""
Normalizes LEGI data stored in an SQLite DB
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from functools import reduce
import json

from .titles import NATURE_MAP_R_SD, gen_titre, normalize_title, parse_titre
from .utils import (
    connect_db, filter_nonalnum, nonword_re, strip_down, strip_prefix,
    upper_words_percentage,
)


def main(db):

    TEXTES_VERSIONS_BRUTES_BITS = {
        'nature': 1,
        'titre': 2,
        'titrefull': 4,
        'autorite': 8,
        'num': 16,
        'date_texte': 32,
    }

    update_counts = {}
    def count_update(k):
        try:
            update_counts[k] += 1
        except KeyError:
            update_counts[k] = 1

    updates = {}
    orig_values = {}
    q = db.all("""
        SELECT id, titre, titrefull, titrefull_s, nature, num, date_texte, autorite
          FROM textes_versions
    """)
    for row in q:
        text_id, titre_o, titrefull_o, titrefull_s_o, nature_o, num, date_texte, autorite = row
        titre, titrefull, nature = titre_o, titrefull_o, nature_o
        len_titre = len(titre)
        if len(titrefull) > len_titre:
            if titrefull[len_titre:][:1] != ' ' and titrefull[:len_titre] == titre:
                # Add missing space
                titrefull = titre + ' ' + titrefull[len_titre:]
        titre, titrefull = normalize_title(titre), normalize_title(titrefull)
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
            def anomaly_cb(titre, k, v1, v2):
                print('Incohérence: ', k, ': "', v1, '" ≠ "', v2, '"\n'
                      '       dans: "', titre, '"', sep='')
                anomaly[0] = True
            d1, endpos1 = parse_titre(titre, anomaly_cb)
            if not d1 and titre != 'Annexe' or d1 and endpos1 < len_titre:
                print('Fail: regex did not fully match titre "', titre, '"', sep='')
            d2, endpos2 = parse_titre(titrefull, anomaly_cb)
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
                    if key == 'calendar':
                        return 'republican'
                    print('Incohérence: ', key, ': "', g1, '" ≠ "', g2, '"\n',
                          '      titre: "', titre, '"\n',
                          '  titrefull: "', titrefull, '"',
                          sep='')
                    anomaly[0] = True
                annexe = get_key('annexe', ignore_not_found=True)
                nature_d = strip_down(get_key('nature'))
                nature_d = NATURE_MAP_R_SD.get(nature_d, nature_d).upper()
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
                            if '-' in num_d or nature == 'DECISION':
                                orig_values['num'] = num
                                updates['num'] = num = num_d
                                count_update('num')
                    elif num[-1] == '.' and num[:-1] == num_d:
                        orig_values['num'] = num
                        updates['num'] = num = num_d
                        count_update('num')
                    else:
                        print('Incohérence: numéro: "', num_d, '" (detecté) ≠ "', num, '" (donné)', sep='')
                        anomaly[0] = True
                date_texte_d = get_key('date')
                calendar = get_key('calendar')
                if date_texte_d:
                    if not date_texte or date_texte == '2999-01-01':
                        orig_values['date_texte'] = date_texte
                        updates['date_texte'] = date_texte = date_texte_d
                        count_update('date_texte')
                    elif date_texte_d != date_texte:
                        print('Incohérence: date: "', date_texte_d, '" (detectée) ≠ "', date_texte, '" (donnée)', sep='')
                        anomaly[0] = True
                autorite_d = get_key('autorite', ignore_not_found=True)
                if autorite_d:
                    autorite_d = strip_down(autorite_d)
                    if not autorite_d.startswith('ministeriel'):
                        autorite_d = strip_prefix(autorite_d, 'du ').upper()
                        if not autorite:
                            orig_values['autorite'] = autorite
                            updates['autorite'] = autorite = autorite_d
                            count_update('autorite')
                        elif autorite != autorite_d:
                            print('Incohérence: autorité "', autorite_d, '" (detectée) ≠ "', autorite, '" (donnée)', sep='')
                            anomaly[0] = True
                if not anomaly[0]:
                    titre = gen_titre(annexe, nature, num, date_texte, calendar, autorite)
                    len_titre = len(titre)
                    titrefull_p2 = titrefull[endpos2:]
                    if titrefull_p2 and titrefull_p2[0] != ' ':
                        titrefull_p2 = ' ' + titrefull_p2
                    titrefull = titre + titrefull_p2
        titrefull_s = filter_nonalnum(titrefull)
        if titre != titre_o:
            count_update('titre')
            orig_values['titre'] = titre_o
            updates['titre'] = titre
        if titrefull != titrefull_o:
            count_update('titrefull')
            orig_values['titrefull'] = titrefull_o
            updates['titrefull'] = titrefull
        if nature != nature_o:
            count_update('nature')
            orig_values['nature'] = nature_o
            updates['nature'] = nature
        if titrefull_s != titrefull_s_o:
            updates['titrefull_s'] = titrefull_s
        if updates:
            db.update("textes_versions", dict(id=text_id), updates)
            updates.clear()
            if orig_values:
                # Save the original non-normalized data in textes_versions_brutes
                bits = (TEXTES_VERSIONS_BRUTES_BITS[k] for k in orig_values)
                orig_values['bits'] = reduce(int.__or__, bits)
                orig_values.update(db.one("""
                    SELECT id, dossier, cid, mtime
                      FROM textes_versions
                     WHERE id = ?
                """, (text_id,), to_dict=True))
                db.insert("textes_versions_brutes", orig_values, replace=True)
                orig_values.clear()

    print('Done. Updated %i values: %s' %
          (sum(update_counts.values()), json.dumps(update_counts, indent=4)))


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    args = p.parse_args()

    db = connect_db(args.db)
    try:
        with db:
            main(db)
    except KeyboardInterrupt:
        pass
