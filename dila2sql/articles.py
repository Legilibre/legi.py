"""
Parsing of article numbers and titles.
"""

from argparse import ArgumentParser
import re

from .roman import ROMAN_PATTERN as roman_num
from .utils import connect_db, show_match


article_num_extra = (
    r"(?:un|duo|ter|quater|quin|sex|sept|octo|novo)?(?:dec|vic|tric|quadrag|quinquag|sexag|septuag|octog|nonag)i[eè]s|"
    r"semel|bis|ter|quar?ter|(?:quinqu(?:edec)?|sext?|sept|oct|non)i[eè]s|quinto"
)  # "quinquedecies" et "sexties" ne sont pas corrects mais existent dans LEGI

article_num = (
    r"(?:"
        r"(?:LO\.? ?|[RD]\*{1,2}|[LDRA]\.? ?)?(?:[0-9]+|1er)|"
        r"[0-9]+[a-z]?|"
        r"\b[A-Z][0-9]*'?|"
        r"\b%(roman_num)s\(?[a-e]?\)?|"
        r"\b(?!AOC|ART\.)[A-Z]{1,4}"  # e.g. LEGIARTI000025170742, LEGIARTI000029180938
    r")(?:"
        r"[-./*](?: ?[0-9]+[A-Z]?| ?[A-Z]{1,4}[0-9]*| ?[a-z])|"
        r" - [0-9]+|"
        r" (?!ART\.)[A-Z0-9]{1,3}|"
        r" [a-z][A-Z]?(?![\w'])|"
        r" ?\((?:%(roman_num)s|[A-Za-z0-9]{1,2})\)|"
        r" 1er|"
        r"[- ](?:%(article_num_extra)s)(?:-[0-9]+)?"
    r")*(?!\w)"
) % globals()

article_type = (
    r"[Aa]dditif |[Aa]nnexes?(?: [:-]|,)? (?:(?:à l')?article |art\. |unique )?|"
    r"[Aa]ppendices? |[Bb]arèmes? |[Dd]otations? |[Dd][ée]cision |[Ll]istes? |"
    r"[Rr]ègle |[Tt]able(?:aux?)? |[Éé]tats? |[Ii]nstruction "
)

article_subtype = (
    r"doc|table(?:au)?|option|état|liste|appendice|"
    r"(?:à|de) l'art(?:\.|icle)|"
    r"(?:au %(roman_num)s )?art(?:\.|icle)?|"
    r"(?:[Ss]ous-)?[Pp]art(?:ie)?"
) % dict(roman_num=roman_num)

article_titre = (
    r"(?:(?:%(article_type)s)(?:technique )?)?"
    r"(?:[nN]° ?)?"
    r"\(?(?:unique|liminaire|(?:suite |-)?%(article_num)s|suite)\)?"
    r"(?: (?:aux articles|art) %(article_num)s(?:(?:,|,? et| à) %(article_num)s)+)?"
    r"(?: (?:[Ss]ous-)?[Pp]arties %(article_num)s(?:(?:,|,? et| à) %(article_num)s)+)?"
    r"(?:,? ?\(?(?:%(article_subtype)s) %(article_num)s\)?)*"
    r"(?: de l'annexe(?: %(article_num)s)?| du statut annexe)?"
    r"(?: \([^)]+\))*"
    r"(?:,? (?:introduction|suite|nouveau|ancien|[Aa]nnexe|[Pp]réambule)$)?"
) % globals()

article_num_multi_1 = (
    r"(?:Annexes?,? (?:%(article_num)s )?)?(?:- )?(?:art(?:\.|icle) )?(%(article_num)s)"
    r"(?:(,? à (?!l'art)|,? et |, ?)(?:(?:art(?:\.|icle) )?((?:[Aa]nnexe )?%(article_num)s)|([Aa]nnexe)$))+"
    r"(?P<incomplete>,$|, art?$)?"
) % globals()

article_num_multi_2 = (
    r"Annexes? \((%(article_num)s)(?:(,? à |,? et |, ?)(%(article_num)s))+\)"
) % globals()

article_num_multi_sub = r"^([0-9]+)(?:(?: \(|, )(\1-[0-9]+(?:(?:,| et) \1-[0-9]+)+)\)?)$"
# Exemples:
# - "13, 13-1, 13-2, 13-3, 13-4" (LEGIARTI000006864199)
# - "15 (15-1 et 15-2)" (LEGIARTI000006864203)

article_num_multi = (
    r"(?:%(article_num_multi_1)s|%(article_num_multi_2)s|%(article_num_multi_sub)s)"
) % globals()


article_num_re = re.compile(article_num)
article_num_extra_re = re.compile(r"\b(?:%s)\b" % article_num_extra, re.I)
article_titre_re = re.compile(article_titre)


def article_num_to_title(num):
    """Turn a raw article number into an article title suitable for display.

    >>> article_num_to_title('1er')
    'Article 1er'
    >>> article_num_to_title('B')
    'Article B'
    >>> article_num_to_title('unique')
    'Article unique'
    >>> article_num_to_title('Annexe')
    'Annexe'
    """
    if article_num_re.match(num) or num[0].islower():
        return 'Article ' + num
    return num


def legifrance_url_article(id, cid):
    return 'https://www.legifrance.gouv.fr/affichCodeArticle.do?idArticle=%s&cidTexte=%s' % (id, cid)


def test_article_num_parsing(db, limit):
    i = 0
    q = db.execute_sql("""
        SELECT id, cid, num
          FROM articles
         WHERE num IS NOT NULL
           AND num <> ''
    """)
    for article_id, cid, num in q:
        if '(' in num or ')' in num:
            num = num.replace('(', '').replace(')', '')
        m = article_titre_re.match(num)
        if not m:
            if article_num_re.search(num):
                print(repr(num), ' ', legifrance_url_article(article_id, cid))
                i += 1
                if i > limit:
                    break
        elif len(m.group(0)) != len(num):
            matched = m.group(0)
            if matched.isdigit():
                n = int(matched)
                if num == '%i - %i' % (n, n + 1):
                    # exemple: "25 - 26", LEGIARTI000006364359
                    continue
            print(repr(show_match(m)), ' ', legifrance_url_article(article_id, cid))
            i += 1
            if i > limit:
                break


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('-l', '--limit', type=int, default=float('inf'))
    args = p.parse_args()

    db = connect_db(args.db)
    with db:
        test_article_num_parsing(db, args.limit)
