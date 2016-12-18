# encoding: utf8

from __future__ import division, print_function, unicode_literals

import re

from .fr_calendar import (
    MOIS_GREG, MOIS_REPU, convert_date_to_iso, gregorian_to_republican,
)
from .roman import decimal_to_roman
from .utils import spaces_re, strip_down


AUTORITE_MAP = {
    "CONSEIL D'ETAT": "du Conseil d'État",
    "ROI": "du Roi",
}

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
NATURE_MAP_R_SD = {strip_down(v): k for k, v in NATURE_MAP.items()}

jour_p = r'(?P<jour>1er|[0-9]{1,2})'
mois_p = r'(?P<mois>%s)' % '|'.join(MOIS_GREG+MOIS_REPU)
annee_p = r'(?P<annee>[0-9]{4,}|an [IVX]+)'
numero_re = re.compile(r'n°(?!\s)', re.U)
premier_du_mois = re.compile(r'\b1 %(mois_p)s %(annee_p)s' % globals())

ordure_p = r'quinquennale?'
annexe_p = r"(?P<annexe>Annexe (au |à la |à l'|du ))"
autorite_p = r'(?P<autorite>ministériel(le)?|du Roi|du Conseil d\'[EÉ]tat)'
date_p = r'(du )?(?P<date>(%(jour_p)s )?%(mois_p)s( %(annee_p)s)?)( (?P=annee))?' % globals()
nature_p = r'(?P<nature>Arr[êe]t[ée]|Code|Constitution|Convention|Décision|Déclaration|Décret(-loi)?|Loi( constitutionnelle| organique)?|Ordonnance)'
nature_strict_p = r'(?P<nature>Arrêté|Code|Constitution|Convention|Décision|Déclaration|Décret(-loi)?|Loi( constitutionnelle| organique)?|Ordonnance)'
nature2_re = re.compile(r'(?P<nature2> (constitutionnelle|organique))', re.U | re.I)
numero_p = r'(n° ?)?(?P<numero>[0-9]+([\-–][0-9]+)*(, ?[0-9]+(-[0-9]+)*)*( et autres)?)\.?'
titre1_re = re.compile(r'(%(annexe_p)s)?(%(nature_p)s)?' % globals(), re.U | re.I)
titre1_strict_re = re.compile(r'(%(annexe_p)s)?%(nature_strict_p)s' % globals(), re.U | re.I)
titre2_re = re.compile(r' ?(%(autorite_p)s|\(?%(date_p)s\)?|%(numero_p)s|%(ordure_p)s)' % globals(), re.U | re.I)
titre2_strict_re = re.compile(r'( %(autorite_p)s| \(?%(date_p)s\)?| %(numero_p)s| %(ordure_p)s)' % globals(), re.U | re.I)


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
        gregorian = '%s %s %s' % (day, MOIS_GREG[month-1], year)
        if calendar == 'republican':
            year, month, day = gregorian_to_republican(year, month, day)
            titre += ' du %s' % day
            if month:
                titre += ' ' + month
            titre += ' an ' + decimal_to_roman(year)
            titre += ' (%s)' % gregorian
        else:
            assert calendar == 'gregorian'
            titre += ' du %s' % gregorian
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
    title = title.replace('constitutionel', 'constitutionnel')
    return title


def parse_titre(titre, anomaly_callback, strict=False):
    m = (titre1_strict_re if strict else titre1_re).match(titre)
    if not m:
        return {}, 0
    d = m.groupdict()
    duplicates = set()
    t2_re = titre2_strict_re if strict else titre2_re
    while True:
        pos = m.end()
        m = t2_re.match(titre, pos)
        if not m:
            if strip_down(d.get('nature', '')) == 'loi':
                m = nature2_re.match(titre, pos)
                if m:
                    d['nature'] += m.group('nature2')
                    pos = m.end()
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
            anomaly_callback(titre, k, d[k], v)
            duplicates.add(k)
            d.pop(k)
