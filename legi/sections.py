"""
Parsing of section titles.
"""

import re

from .articles import article_num, article_num_extra
from .french import ordinals_p, long_ordinals_p, short_ordinals_p, get_clean_ordinal
from .roman import ROMAN_PATTERN as roman_num
from .utils import add_accentless_fallbacks, strip_down


SPECIAL_NUMS = ["unique", "préliminaire", "liminaire"]
SPECIAL_NUMS_MAP = {strip_down(word): word for word in SPECIAL_NUMS}
special_nums_p = '|'.join(SPECIAL_NUMS)

section_num_strict_p = (
    r"(?<!\w)(?:"
        r"%(special_nums_p)s|"
        r"(?:%(ordinals_p)s|[0-9]+(?: ?°)?|0*%(roman_num)s|0*[A-Za-z])"
        r"(?:"
            r"[-./* ] ?(?:[0-9]+|[A-Za-z]\b|%(roman_num)s|%(article_num_extra)s)|"
            r"\.? - [0-9]+"
        r")*"
    r")(?![\w'])"
) % dict(
    article_num_extra=article_num_extra, ordinals_p=ordinals_p,
    roman_num=roman_num, special_nums_p=special_nums_p,
)

section_num_p = r"(?i:%s)" % add_accentless_fallbacks(section_num_strict_p)

section_ord_strict_p = (
    r"(?:%s|%s)"
) % (long_ordinals_p.title(), short_ordinals_p)

section_ord_p = r"(?i:%s)" % add_accentless_fallbacks(section_ord_strict_p)

section_type_strict_p = (
    r"(?:Sous[- ])*(?:"
    r"Annexes?|Appendice|Avenant|Chapitre|Division|État|Livre|Paragraphe|§|"
    r"Partie|Préambule|Section|Tableaux?|Titre"
    r")"
)

section_type_p = r"(?i:%s)" % add_accentless_fallbacks(section_type_strict_p)

section_p = (
    r"(?P<ord>%(section_ord_p)s )?"
    r"(?P<type>%(section_type_p)s)?"
    r"(?(ord)|(?(type)\s|)(?i:n° ?)?(?P<num>%(section_num_p)s(?: (?:et|à) %(section_num_p)s)?))"
    r"(?:"
        r"(?P<article> (?:mentionnée )?à l'article %(article_num)s)|"
        r"(?P<relatif> relatif au livre %(section_num_p)s)"
    r")?"
) % dict(
    article_num=article_num, section_num_p=section_num_p,
    section_ord_p=section_ord_p, section_type_p=section_type_p,
)

section_re = re.compile(section_p)

sujet_re = re.compile((
    r"(?:[.)]\s*(?:[-:]\s+)?|\s*[-:]\s*|\s+[-:]|\s+\(|\s+(?=[A-ZÇÉ]|\w+ant ))"
    r"(.+)"
), re.DOTALL)


def legifrance_url_section(id, cid):
    return 'https://www.legifrance.gouv.fr/affichCode.do?idSectionTA=%s&cidTexte=%s' % (id, cid)


def lower(m):
    return m.group(0).lower()


space_inside_num_re = re.compile((
    r"%(roman_num)s(\.? -? ?| ?- )[0-9]+"
) % dict(roman_num=roman_num))


def remove_spaces(m):
    return m.group(0).replace(m.group(1), '-')


ordinal_re = re.compile(r"\b%s\b" % add_accentless_fallbacks(ordinals_p))


def normalize_section_num(num):
    if not num:
        return num
    num = space_inside_num_re.sub(remove_spaces, num)
    num = ordinal_re.sub(get_clean_ordinal, num)
    num_sd = strip_down(num)
    if num_sd in SPECIAL_NUMS_MAP:
        num = SPECIAL_NUMS_MAP[num_sd]
    return num


def reduce_section_title(titre_ta):
    """Reduce a section title to its "first half".

    >>> reduce_section_title("Titre 1er: Dispositions générales")
    'Titre 1er'
    >>> reduce_section_title("Première partie")
    'Première partie'
    >>> print(reduce_section_title("Dispositions finales"))
    None

    This function assumes that the section title has already been normalized.
    """
    m = section_re.match(titre_ta)
    if m and (m.end() == len(titre_ta) or sujet_re.match(titre_ta, m.end())):
        return m.group(0).rstrip('.°')
