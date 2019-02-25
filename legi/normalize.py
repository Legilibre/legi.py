"""
Normalizes LEGI data stored in an SQLite DB
"""

from argparse import ArgumentParser
from collections import defaultdict
from functools import reduce
import json
import re

from .articles import (
    article_num, article_num_extra_re, article_num_multi, article_num_multi_sub,
    article_titre, legifrance_url_article,
)
from .french import get_clean_ordinal
from .html_utils import bad_space_re, drop_bad_space, split_first_paragraph, escape, unescape
from .roman import ROMAN_PATTERN as roman_num
from .sections import (
    legifrance_url_section, normalize_section_num, reduce_section_title,
    section_re, section_type_p, sujet_re,
)
from .titles import NATURE_MAP_R_SD, gen_titre, normalize_title, parse_titre
from .utils import (
    ascii_spaces_re, connect_db, filter_nonalnum, mimic_case, nonword_re,
    show_match, strip_down, strip_prefix, upper_words_percentage,
)


dash_re = re.compile(r"[\u2012-\u2015]")


missing_accent_re = re.compile(r"(Annexe|relatif)( a )(?=l'\w{3,} |la \w{3,} )", re.I)


def add_accent(m):
    return m.group(1) + mimic_case(m.group(2), ' à ')


quotes_re = re.compile(r'(^| )"([^"]+)"(?=\W|$)', re.U)


def replace_quotes(m):
    return '%s« %s »' % (m.group(1), m.group(2).strip())


upper_word_re = re.compile((
    r"\b(?!AOC |FRA\. |%s(?:[ ,;:.)-]|$))(?:À|(?:[DL]')?[A-ZÀÂÇÈÉÊËÎÔÛÜ]{2,})\b"
) % roman_num, re.U)


def lower(m):
    return m.group(0).lower()


def normalize_article_numbers(db, dry_run=False, log_file=None):
    print("> Normalisation des numéros des articles...")

    article_num_multi_re = re.compile(article_num_multi)
    article_num_multi_sub_re = re.compile(article_num_multi_sub)
    article_titre_partial_re = re.compile(r"^%s(?!\w)" % article_titre, re.U)

    space_around_dash_re = re.compile((
        r"(?:[0-9]+|%(roman_num)s)(?:- | -)(?:[0-9]+|%(roman_num)s\b)"
    ) % dict(roman_num=roman_num))

    extraneous_dash_re = re.compile(r" -(%(article_num)s)" % globals())

    WORD_CORRECTIONS = {
        'equivalence': 'équivalence',
        'etat': 'état',
        'execution': 'exécution',
        'metier': 'métier',
        'preambule': 'préambule',
        'referentiel': 'référentiel',
    }
    word_correction_re = re.compile(r"\b(%s)(s?)\b" % '|'.join(WORD_CORRECTIONS), re.I)

    def word_corrector(m):
        word = m.group(1)
        correct_word = WORD_CORRECTIONS.get(word.lower())
        return mimic_case(word, correct_word) + m.group(2)

    missing_space_re = re.compile(r"\b(%s)(\((?:[A-Z]{2}|suite)\))" % roman_num)

    def add_missing_space(m):
        return '%s %s' % m.groups()

    TITLE_REPLACEMENTS = {
        'LEGIARTI000006326743': "",
        'LEGIARTI000006804495': "Annexe 1 à l'article R513-7",
        'LEGIARTI000006804497': "Annexe 2 à l'article R513-7",
        'LEGIARTI000006831539': 'Annexe IV bis',
        'LEGIARTI000006893436': "Annexe II",
        'LEGIARTI000006934477': "Articles 3 bis, 4 à 16, 16 bis à 16 sexies",
        'LEGIARTI000006934489': "Annexes II à X",
        'LEGIARTI000006570272':
            "Annexe I : Tableau d'équivalence des classes et échelons de sous-préfet et d'administrateur civil",
        'LEGIARTI000019895551':
            "Annexe II : Tableau relatif à l'avancement d'échelon des sous-préfets",
        'LEGIARTI000019151586': "Annexe II : Habitats humides",
        'LEGIARTI000021189469': "Annexe 1 : AOC «\xa0Moulis\xa0»",
        'LEGIARTI000023411984': "Annexe I : Hépatite B",
        'LEGIARTI000023411988': "Annexe II : Hépatite C",
    }

    case_normalization_re = re.compile((
        r"\b("
        r"annex[eé]s?|art(?:icle)?|tableaux?|états?|introduction|préambule|addendum|"
        r"appendice|informative|législatifs?|extraits|directive|technique"
        r")\b"
    ), re.I)

    def normalize_case(m):
        word = m.group(1)
        if m.start(1) == 0:
            return word.title()
        else:
            return word.lower() if word.isupper() else word

    annexe_num_double_re = re.compile((
        r"Annexe à l'article (%(article_num)s(?: \([^)]+\))?) Annexe (%(article_num)s)"
    ) % dict(article_num=article_num))

    special_case_re = re.compile((
        r"(AOC|FRA\.)( (?:« )?[A-ZÀÂÇÈÉÊËÎÔÛÜ-]{2,}(?: [A-ZÀÂÇÈÉÊËÎÔÛÜ-]{2,})*)"
    ), re.U)

    def special_case_sub(m):
        return m.group(1) + m.group(2).title()

    annexe_suffix_re = re.compile((
        r"^(?P<art_num>(?=[LDRA])%(article_num)s),? [Aa]nnexe(?: (?P<annexe_num>%(roman_num)s|[0-9]+))?$"
    ) % globals())

    article_position_re = re.compile((
        r"(?:ANNEXE(?: %(article_num)s)?,? )?"
        r"(?:\(?(?:"
            r"(?:CHAPITRE|PAR(?:\.|AGRAPHE)|TITRE|PARTIE)(?: %(article_num)s)?|"
            r"(?:PREMIERE|DEUXIEME|TROISIEME) PARTIE"
        r")\)?(?:,? |$))+"
        r"(?:(?P<article>ART(?:\.|ICLE) )?(?P<num>[0-9]+)\.?|(?P<intro>INTRODUCTION))?"
    ) % dict(article_num=article_num))

    standard_num_with_garbage_re = re.compile(
        r"\b(LO|[RD]\*{1,2}|[LDRA])(?:\. ?|\.? )([0-9]{3,})\b"
    )
    def drop_garbage(m):
        return m.group(1) + m.group(2)

    range_re = re.compile(r"^\([0-9]+ à [0-9]+\)")

    counts = defaultdict(int)
    def count(k, n=1):
        counts[k] += n

    changes = defaultdict(int)
    def add_change(k):
        assert k[0] != k[1]
        changes[k] += 1
        if dry_run:
            return
        update_article({'num': k[1]})

    def update_article(data):
        if dry_run:
            return
        db.update('articles', {'id': article_id}, data)

    q = db.all("""
        SELECT id, cid, num
          FROM articles
         WHERE length(num) > 0
    """)
    for article_id, cid, orig_num in q:
        num = orig_num
        if ascii_spaces_re.search(num):
            num = ascii_spaces_re.sub(' ', num)
        if '*suite*' in num:
            num = num.replace('*suite*', '(suite)')  # exemple: LEGIARTI000006668354
        if num and num[0] == '*' and num[-1] == '*':
            num = num.strip('*')
        if 'à Lot-et-G.' in num:
            num = num.replace('à Lot-et-G.', 'à Lot-et-Garonne')
        num = num.strip(' .:')
        if not num:
            count('empty')
            add_change((orig_num, num))
            continue

        if " à L'article " in num:
            num = num.replace(" à L'article ", " à l'article ")
        if '–' in num:
            num = num.replace('–', '-')
        if ',,' in num:
            num = num.replace(',,', ',')
        if space_around_dash_re.search(num):
            num = space_around_dash_re.sub(drop_bad_space, num)
        if extraneous_dash_re.search(num):
            # exemple: "ANNEXE -IV" (LEGIARTI000006535355)
            num = extraneous_dash_re.sub(r' \1', num)
        if num.startswith('AOC ') and '..' in num:
            # exemple: 'AOC " Côtes du Roussillon .."' (LEGIARTI000021231010)
            num = num.replace('..', '')
        if bad_space_re.search(num):
            num = bad_space_re.sub(drop_bad_space, num)
        if quotes_re.search(num):
            num = quotes_re.sub(replace_quotes, num)
        if standard_num_with_garbage_re.search(num):
            num = standard_num_with_garbage_re.sub(drop_garbage, num)
        if num[1:3] == '.-':
            # exemple: LEGIARTI000036496662
            num = num.replace('.-', '-')
        if num != orig_num:
            count('removed or replaced bad character(s)')

        if article_id in TITLE_REPLACEMENTS:
            num = TITLE_REPLACEMENTS[article_id]
            if num != orig_num:
                count('replaced num (hardcoded)')
                add_change((orig_num, num))
            continue
        elif num == '(suite Ib)':  # LEGIARTI000030127261
            num = 'Ib (suite)'
            count('corrected (suite)')
        elif cid == 'LEGITEXT000006074493' and num.endswith(' STATUT ANNEXE'):
            num = num.replace(' STATUT ANNEXE', ' du statut annexe')
            count('corrected (statut annexe)')
        elif cid == 'JORFTEXT000020692049' and range_re.match(num):
            num = "Tableau annexe - départements %s" % num[1:-1]
            count('replaced split article num (hardcoded)')
        elif cid == 'JORFTEXT000027513723' and num == 'Annexe IIII':
            num = 'Annexe III'
            count('fixed annexe num (hardcoded)')
        elif cid == 'JORFTEXT000000325199' and num.endswith(', annexe'):
            num = num[:-8]
            count('removed suffix \'annexe\' (hardcoded)')
        elif cid == 'JORFTEXT000000735207' and num == 'annexe ii':
            num = 'Annexe II'
            count('uppercased roman number (hardcoded)')

        first_word = num[:num.find(' ')]
        if first_word.lower() == 'article':
            num = num[8:]
            count('dropped first word \'article\'')

        if 'ANNEXE' in num:
            if num == 'ANNEXE TABLEAU':
                num = 'Tableau annexe'
                count('lowercased, and reversed word order')
            else:
                num = num.replace("ANNEXE A L'ARTICLE", "Annexe à l'article")
                num = num.replace(" ET ANNEXE", " et annexe")
                num = num.replace("ANNEXE N°", "Annexe n°")
                num = num.replace("ANNEXE(s)", "Annexes")
                num = num.replace("ANNEXES( 1)", "Annexes (1)")
                if num != orig_num:
                    count('recased \'ANNEXE\'')

        position_match = article_position_re.match(num)
        if position_match:
            if len(position_match.group(0)) != len(num):
                print("Warning: capture partielle (article_position_re): %r" % show_match(position_match))
            # texte mal découpé, exemple: JORFTEXT000000316939
            if position_match.group('article'):
                num = position_match.group('num')
                assert num
            elif position_match.group('intro'):
                num = 'Introduction'
            else:
                num = ''
            count('dropped position')

        if missing_space_re.search(num):
            num = missing_space_re.sub(add_missing_space, num)
            count('added missing space')

        if word_correction_re.search(num):
            num = word_correction_re.sub(word_corrector, num)
            count('added missing accent(s)')

        if article_num_extra_re.search(num):
            num = article_num_extra_re.sub(lower, num)
            if num != orig_num:
                count('lowercased (extra)')

        if case_normalization_re.search(num):
            num2 = case_normalization_re.sub(normalize_case, num)
            if article_titre_partial_re.match(num2) or not upper_word_re.search(num2):
                num = num2
                if num != orig_num:
                    count('normalized case')
            del num2

        if special_case_re.search(num):
            num = special_case_re.sub(special_case_sub, num)
            if num != orig_num:
                count('titlecased')
                add_change((orig_num, num))
            continue
        else:
            is_title = (
                num[:4] in ('AOC ', 'FRA.', 'CA d', 'TPI ') or
                num == 'CA Aix-en-Provence' or
                num.startswith('Annexe AOC ')
            )
            if is_title:
                count('skipped detected title')
                if num != orig_num:
                    add_change((orig_num, num))
                continue

        if cid == 'LEGITEXT000006074201' and num.lower().startswith('annexe 22, '):
            num = "%s de l'annexe 22" % num[len('ANNEXE 22, '):]
            count('moved prefix \'annexe\' to suffix (hardcoded)')

        annexe_suffix_match = annexe_suffix_re.match(num)
        if annexe_suffix_match:
            matches = annexe_suffix_match.groupdict()
            if matches['annexe_num']:
                num = "Annexe %(annexe_num)s à l'article %(art_num)s" % matches
            else:
                num = "Annexe à l'article %(art_num)s" % matches
            del matches
            count('moved suffix \'annexe\' to prefix')

        multi_num_match = article_num_multi_re.match(num)
        if multi_num_match:
            base_num_match = article_num_multi_sub_re.match(num)
            if base_num_match:
                num = "%s (%s)" % (base_num_match.group(1), base_num_match.group(2))
                count('split base number and aliases')
                add_change((orig_num, num))
                continue
            if len(multi_num_match.group(0)) != len(num):
                url = legifrance_url_article(article_id, cid)
                print("Warning: capture partielle de multiples numéros: %r   %s" %
                      (show_match(multi_num_match), url))
            count('detected a multi-article')
            if num != orig_num:
                add_change((orig_num, num))
            continue

        if annexe_num_double_re.search(num):
            num = annexe_num_double_re.sub(r"Annexe \2 à l'article \1", num)
            count('collapsed double number')
            add_change((orig_num, num))
            continue

        m = article_titre_partial_re.match(num)
        if m:
            is_full_match = len(m.group(0)) == len(num)
            if not is_full_match:
                offset = m.end(0)
                part2 = num[offset:]
                is_full_match = (
                    part2[:3] == ' : ' or
                    part2.startswith(' relative ') or
                    part2.startswith(' relatif ')
                )
                if is_full_match:
                    if upper_words_percentage(part2) > 0.2:
                        count('detected a bad title (uppercase)')
                elif part2.startswith(' aux articles '):
                    # titre tronqué, on essaye de le compléter en extrayant le
                    # premier paragraphe du contenu de l'article
                    html = db.one(
                        "SELECT bloc_textuel FROM articles WHERE id = ?", (article_id,)
                    )
                    paragraph, rest = split_first_paragraph(html)
                    paragraph = paragraph.replace('\n', ' ')
                    m3 = article_titre_partial_re.match(paragraph)
                    if m3 and paragraph.startswith(orig_num) and len(m3.group(0)) == len(paragraph):
                        num = standard_num_with_garbage_re.sub(drop_garbage, paragraph)
                        add_change((orig_num, num))
                        assert rest
                        update_article({'bloc_textuel': rest})
                        count('completed truncated title, and removed it from bloc_textuel')
                        continue
                    url = legifrance_url_article(article_id, cid)
                    if m3:
                        print("Warning: échec de la récupération du titre: %r   %s" % (show_match(m3), url))
                    else:
                        print("Warning: échec de la récupération du titre: %r   %s" % (paragraph, url))
            if is_full_match:
                count('article_titre regexp matched')
            else:
                count('article_titre regexp did not match')
                url = legifrance_url_article(article_id, cid)
                print("Warning: capture partielle du numéro: %r   %s" % (show_match(m), url))

        if num != orig_num:
            add_change((orig_num, num))

    if log_file:
        log_file.write("# numéros d'articles\n")
        for change, count in sorted(changes.items()):
            if count == 1:
                log_file.write('%r => %r\n' % change)
            else:
                log_file.write('%r => %r (%i×)\n' % (change[0], change[1], count))

    print('Done. Result: ' + json.dumps(counts, indent=4, sort_keys=True))


def normalize_section_titles(db, dry_run=False, log_file=None):
    print("> Normalisation des titres de sections...")

    counts = defaultdict(int)
    def count(k, n=1):
        counts[k] += n

    changes = defaultdict(int)
    def add_change(k):
        if k[0].strip().rstrip('.') == k[1]:
            # Simple trimming isn't worth logging
            return
        changes[k] += 1
        if dry_run:
            return
        update_section({'titre_ta': k[1]})

    def update_section(data):
        if dry_run:
            return
        db.update('sections', {'id': section_id}, data)

    multi_spaces_re = re.compile(r"(?: {2,}|\t+[ \t]*)")

    def replace_multiple_spaces(m):
        if len(m.group(0)) > 3 or '\t' in m.group(0):
            count('replaced multiple spaces with newline')
            return '\n'
        count('collapsed multiple spaces')
        return ' '

    newlines_re = re.compile(r"(?: *\r?\n)+")

    def replace_newline(m):
        try:
            next_char = m.string[m.end()]
        except KeyError:
            return ''
        if (next_char.isalpha() and next_char.islower()) or next_char == ':':
            count('replaced newline with space')
            return ' '
        if m.group(0) != '\n':
            count('collapsed multiple newlines')
        return '\n'

    bad_separator_re = re.compile((
        r"^(%(section_type_p)s (?:[0-9]+|%(roman_num)s)) : (-[0-9]+)(?= [A-ZÇÉ])"
        # e.g. "Sous-section 8 : -1  Ministère …"
    ) % dict(roman_num=roman_num, section_type_p=section_type_p))

    def clean_num_match(m):
        num = ' '.join(filter(None, [
            get_clean_ordinal((m.group('ord') or '').rstrip()),
            (m.group('type') or '').lower().replace('preambule', 'préambule'),
            normalize_section_num(m.group('num') or '')
        ]))
        if m.group('ord') or m.group('type'):
            num = num[0].upper() + num[1:]
        return num

    q = db.all("SELECT id, cid, titre_ta FROM sections")
    for section_id, cid, titre_ta_o in q:
        titre_ta = titre_ta_o
        url = legifrance_url_section(section_id, cid)

        if '&' in titre_ta:
            assert '<' not in titre_ta, titre_ta
            titre_ta = escape(unescape(titre_ta), quote=False)
            count('unescaped HTML entities')

        len_before = len(titre_ta)
        titre_ta = titre_ta.strip(' \t\n\r\f\v:')
        if titre_ta[-1] == '.' and titre_ta[-2] != '.':
            titre_ta = titre_ta[:-1].rstrip()
        if len(titre_ta) != len_before:
            count('trimmed')
            if not titre_ta:
                count('empty')
                if titre_ta != titre_ta_o:
                    add_change((titre_ta_o, titre_ta))
                continue
        del len_before

        titre_ta = multi_spaces_re.sub(replace_multiple_spaces, titre_ta)
        titre_ta = newlines_re.sub(replace_newline, titre_ta)

        titre_ta_before = titre_ta
        titre_ta = dash_re.sub('-', titre_ta)
        titre_ta = quotes_re.sub(replace_quotes, titre_ta)
        if titre_ta != titre_ta_before:
            count('replaced non-standard character(s)')
        del titre_ta_before

        if titre_ta in {'Annexe', 'Annexes'}:
            if titre_ta != titre_ta_o:
                add_change((titre_ta_o, titre_ta))
            continue

        if '\n' in titre_ta:
            count('detected a bad section title (newline)')
        elif '« Art.' in titre_ta:
            count('detected a bad section title (article)')
        elif titre_ta[0] in '"«':
            count('detected a bad section title (quote)')

        if titre_ta.startswith('A N N E X E'):
            if titre_ta.startswith('A N N E X E S'):
                titre_ta = 'ANNEXES' + titre_ta[13:]
            else:
                titre_ta = 'ANNEXE' + titre_ta[11:]
            count('unspaced `A N N E X E`')

        titre_ta, n = bad_separator_re.subn(r'\1\2', titre_ta)
        if n:
            count('removed bad separator', n)

        titre_ta, n = missing_accent_re.subn(add_accent, titre_ta)
        if n:
            count('added missing accent', n)

        if article_num_extra_re.search(titre_ta):
            titre_ta = article_num_extra_re.sub(lower, titre_ta)
            count('lowercased extra')

        num, separator, sujet = [], None, None
        num_end = 0
        while True:
            m = section_re.match(titre_ta, num_end)
            if not m:
                break
            num.append(m)
            num_end = m.end()
            while num_end < len(titre_ta) and titre_ta[num_end] in ' ,;/|':
                num_end += 1

        if num:
            num_end = num[-1].end()
            if len(num) > 1:
                count('multiple matches')
            if num_end == len(titre_ta):
                count('full match')
            else:
                sujet_match = sujet_re.match(titre_ta[num_end:])
                if sujet_match:
                    separator = sujet_match.string[:sujet_match.start(1)]
                    separator = ascii_spaces_re.sub(' ', separator)
                    sujet = sujet_match.group(1)
                    if titre_ta[num_end-1].isalnum() and sujet[0].isupper():
                        if separator in {' : ', ' - ', '. ', ') '}:
                            pass
                        elif separator == ' ':
                            if not sujet[1].isupper():
                                separator = ' : '
                                count('added separator')
                        elif separator[-1] != ' ':
                            separator += ' '
                            count('added space to separator')
                        else:
                            separator = ' : '
                            count('replaced separator')
                    count('good match')
                elif len(num) == 1 and ' ' not in num[0].group(0).strip():
                    # The initial match was probably a false positive, ignore it
                    sujet = titre_ta
                    num = None
                    count('false match')
                else:
                    match = repr(show_match((titre_ta, (0, num_end))))
                    print("Warning: partial match:", match, " ", url)
                    count('partial match')
                    sujet = titre_ta[num_end:]
            if num:
                num = ' '.join(map(clean_num_match, num))
        else:
            sujet = titre_ta
            count('no match')

        if num and upper_word_re.search(num):
            print("Warning: still uppercase: %r" % num, " ", url)
            count('still uppercase (num)')

        if sujet and upper_words_percentage(sujet) > 0.2:
            count('detected a bad section title (uppercase)')

        titre_ta = ''.join(filter(None, (num, separator, sujet)))
        if titre_ta != titre_ta_o:
            add_change((titre_ta_o, titre_ta))

    print("Done. Result: " + json.dumps(counts, indent=4, sort_keys=True))

    if log_file:
        log_file.write("# titres de sections\n")
        for change, count in sorted(changes.items()):
            if count == 1:
                log_file.write('%r => %r\n' % change)
            else:
                log_file.write('%r => %r (%i×)\n' % (change[0], change[1], count))


def normalize_sommaires_num(db, dry_run=False, log_file=None):
    print("> Normalisation des numéros dans les sommaires...")

    counts = {}

    db.run("""
        UPDATE sommaires AS so
           SET num = (
                   SELECT a.num
                     FROM articles a
                    WHERE a.id = so.element
               )
         WHERE substr(so.element, 5, 4) = 'ARTI'
           AND COALESCE(so.num, '') <> (
                   SELECT COALESCE(a.num, '')
                     FROM articles a
                    WHERE a.id = so.element
               )
    """)
    counts['updated num for article'] = db.changes()

    db.create_function('reduce_section_title', 1, reduce_section_title)
    db.run("""
        UPDATE sommaires AS so
           SET num = (
                   SELECT reduce_section_title(s.titre_ta)
                     FROM sections s
                    WHERE s.id = so.element
               )
         WHERE substr(so.element, 5, 4) = 'SCTA'
           AND COALESCE(so.num, '') <> (
                   SELECT reduce_section_title(s.titre_ta)
                     FROM sections s
                    WHERE s.id = so.element
               )
    """)
    counts['updated num for section'] = db.changes()

    print("Done. Result: " + json.dumps(counts, indent=4, sort_keys=True))


def normalize_text_titles(db, dry_run=False, log_file=None):
    print("> Normalisation des titres des textes...")

    TEXTES_VERSIONS_BRUTES_BITS = {
        'nature': 1,
        'titre': 2,
        'titrefull': 4,
        'autorite': 8,
        'num': 16,
        'date_texte': 32,
    }

    counts = defaultdict(int)

    changes = defaultdict(int)
    def add_change(orig_value, new_value):
        if filter_nonalnum(new_value) == filter_nonalnum(orig_value):
            # Not worth logging
            return
        changes[(orig_value, new_value)] += 1

    updates = {}
    orig_values = {}
    q = db.all("""
        SELECT id, titre, titrefull, titrefull_s, nature, num, date_texte, autorite
          FROM textes_versions_brutes_view
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
            counts['failed to normalize titre (still uppercase)'] += 1
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
                nature_complète = get_key('nature')
                nature_d = strip_down(nature_complète)
                nature_d = NATURE_MAP_R_SD.get(nature_d, nature_d).upper()
                if ' ' in nature_d:
                    nature_d = nature_d.split(' ', 1)[0]
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
                        if annexe:
                            # On ne veut pas donner le numéro d'un décret à son annexe,
                            # mais on ne va pas retirer le numéro du titre non plus
                            num = num_d
                        else:
                            if '-' in num_d or nature == 'DECISION':
                                orig_values['num'] = num
                                updates['num'] = num = num_d
                                counts['updated num'] += 1
                    elif num[-1] == '.' and num[:-1] == num_d:
                        orig_values['num'] = num
                        updates['num'] = num = num_d
                        counts['updated num'] += 1
                    else:
                        print('Incohérence: numéro: "', num_d, '" (detecté) ≠ "', num, '" (donné)', sep='')
                        anomaly[0] = True
                date_texte_d = get_key('date')
                calendar = get_key('calendar')
                if date_texte_d:
                    if not date_texte or date_texte == '2999-01-01':
                        orig_values['date_texte'] = date_texte
                        updates['date_texte'] = date_texte = date_texte_d
                        counts['updated date_texte'] += 1
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
                            counts['updated autorite'] += 1
                        elif autorite != autorite_d:
                            print('Incohérence: autorité "', autorite_d, '" (detectée) ≠ "', autorite, '" (donnée)', sep='')
                            anomaly[0] = True
                if not anomaly[0]:
                    titre = gen_titre(annexe, nature_complète, num, date_texte, calendar, autorite)
                    len_titre = len(titre)
                    titrefull_p2 = titrefull[endpos2:]
                    if titrefull_p2 and titrefull_p2[0].isalnum():
                        titrefull_p2 = ' ' + titrefull_p2
                    titrefull = titre + titrefull_p2
                    if num and titrefull.count(num) != 1:
                        print((
                            "Échec: `num` apparaît %i fois dans le `titrefull`: %r\n"
                            "             construit à partir de `titrefull_o`: %r\n"
                            "                                 et de `titre_o`: %r"
                        ) % (titrefull.count(num), titrefull, titrefull_o, titre_o))
        if titrefull != titre and upper_words_percentage(titrefull) > 0.5:
            counts['detected a bad titrefull (uppercase)'] += 1
        if quotes_re.search(titrefull):
            titrefull = quotes_re.sub(replace_quotes, titrefull)
            counts['normalized quotes in titrefull'] += 1
        titrefull_s = filter_nonalnum(titrefull)
        if titre != titre_o:
            counts['updated titre'] += 1
            orig_values['titre'] = titre_o
            updates['titre'] = titre
            add_change(titre_o, titre)
        if titrefull != titrefull_o:
            counts['updated titrefull'] += 1
            orig_values['titrefull'] = titrefull_o
            updates['titrefull'] = titrefull
            add_change(titrefull_o, titrefull)
        if nature != nature_o:
            counts['updated nature'] += 1
            orig_values['nature'] = nature_o
            updates['nature'] = nature
        for col, new_value in updates.items():
            orig_value = orig_values[col]
            assert new_value != orig_value
        if titrefull_s != titrefull_s_o:
            updates['titrefull_s'] = titrefull_s
        if updates:
            if not dry_run:
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
                if not dry_run:
                    db.insert("textes_versions_brutes", orig_values, replace=True)
                orig_values.clear()

    print('Done. Result:', json.dumps(counts, indent=4))

    if log_file:
        log_file.write("# titres de textes\n")
        for change, count in sorted(changes.items()):
            if count == 1:
                log_file.write('%r => %r\n' % change)
            else:
                log_file.write('%r => %r (%i×)\n' % (change[0], change[1], count))


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('what', nargs='?', default='all', choices=[
        'all', 'articles_num', 'sections_titres', 'sommaires_num', 'textes_titres'
    ])
    p.add_argument('--dry-run', action='store_true', default=False)
    p.add_argument('--log-path', default='/dev/null')
    args = p.parse_args()

    db = connect_db(args.db)
    log_file = open(args.log_path, 'w') if args.log_path else None
    try:
        with db:
            if args.what in ('all', 'textes_titres'):
                normalize_text_titles(db, dry_run=args.dry_run, log_file=log_file)
            if args.what in ('all', 'sections_titres'):
                normalize_section_titles(db, dry_run=args.dry_run, log_file=log_file)
            if args.what in ('all', 'articles_num'):
                normalize_article_numbers(db, dry_run=args.dry_run, log_file=log_file)
            if args.what in ('all', 'sommaires_num'):
                normalize_sommaires_num(db, dry_run=args.dry_run, log_file=log_file)
            if args.dry_run:
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
