"""
Constants and functions specific to the French language.
"""

import re

from .roman import ROMAN_PATTERN_SIMPLE as roman_num
from .utils import add_accentless_fallbacks, strip_down


INTRA_WORD_CHARS = "'’.-‐‑–"  # the dot is for abbreviations

ORDINALS = (
    "première|premier|deuxième|seconde|second|troisième|quatrième|cinquième|"
    "sixième|septième|huitième|neuvième|dixième|"
    "onzième|douzième|treizième|quatorzième|quinzième|seizième"
).split('|')

ORDINALS_SD_MAP = {strip_down(o): o for o in ORDINALS}


long_ordinals_p = '|'.join(ORDINALS)
short_ordinals_strict_p = (
    r"([1I])(è?re|er)|(2|II)(n?de?)|([2-9][0-9]*|(?=[MDCLXVI]{2})%s)(è?me|em?)"
) % roman_num
short_ordinals_p = r"(?-i:%s|%s)" % (short_ordinals_strict_p, short_ordinals_strict_p.upper())
ordinals_p = '|'.join((long_ordinals_p, short_ordinals_p))

short_ordinal_re = re.compile(add_accentless_fallbacks(short_ordinals_p))


def get_clean_ordinal(o):
    """Returns a normalized form of a French ordinal.

    >>> get_clean_ordinal('premiere')
    'première'
    >>> get_clean_ordinal('1er')
    '1er'
    >>> get_clean_ordinal('IER')
    'Ier'
    """
    if not o:
        return o
    if type(o) is re.Match:
        o = o.group(0)
    m = short_ordinal_re.fullmatch(o)
    if m:
        num, suffix = filter(None, m.groups())
        return num + suffix.lower()
    return ORDINALS_SD_MAP[strip_down(o)]
