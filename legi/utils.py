import os
import os.path
import re
import sre_parse
import traceback
from unicodedata import combining, decomposition, normalize
from peewee import SqliteDatabase, PostgresqlDatabase, ProgrammingError, IntegrityError
from playhouse.db_url import connect
from datetime import date
from .models import db_proxy, DBMeta


if not hasattr(re, 'Match'):
    # For Python 3.6
    re.Match = type(re.compile('').match(''))


ROOT = os.path.dirname(__file__) + '/'


def connect_db(db_url, create_schema=True, update_schema=True):
    db = connect(db_url)
    db.interpolation_char = '?' if isinstance(db, SqliteDatabase) else "%s"

    if create_schema:
        if not db.table_exists("db_meta"):
            with open(ROOT + 'sql/schema.sql', 'r') as f:
                if isinstance(db, PostgresqlDatabase):
                    db.cursor().execute(f.read())
                elif isinstance(db, SqliteDatabase):
                    db.cursor().executescript(f.read())

    if update_schema:
        r = run_migrations(db)
        if r == '!RECREATE!':
            return connect_db(db_url, create_schema=True)

    return db


def run_migrations(db):
    db_proxy.initialize(db)
    db_meta = DBMeta.select().where(DBMeta.key == 'schema_version').first()
    v = int(db_meta.value) if db_meta else 0
    if v == 0:
        DBMeta.insert(key='schema_version', value=v).execute()
    migrations = open(ROOT + 'sql/migrations.sql').read().split('\n\n-- migration #')
    n = 0
    for m in migrations[1:]:
        n, sql = m.split('\n', 1)
        n = int(n)
        if v >= n:
            continue
        sql = sql.strip()
        if sql == '!RECREATE!':
            print('Recreating DB from scratch (migration #%s)...' % n)
            db.close()
            # TODO
            # os.rename(db.address, db.address + '.back')
            return sql
        print('Running DB migration #%s...' % n)
        try:
            db.cursor().executescript(sql)
        except (IntegrityError, ProgrammingError):
            traceback.print_exc()
            r = input('Have you already run this migration? (y/N) ')
            if r.lower() != 'y':
                raise SystemExit(1)
        DBMeta.update(value=n).where(key='schema_version').execute()
    return n - v


def group_by_2(iterable):
    iterable = iterable.__iter__()
    next = iterable.__next__
    while True:
        try:
            a = next()
        except StopIteration:
            return
        try:
            b = next()
        except StopIteration:
            raise ValueError("iterable returned an odd number of items")
        yield (a, b)


def add_accentless_fallbacks(pattern):
    r"""Modifies a regexp pattern to also match accentless text.

    >>> add_accentless_fallbacks(r'Arrêté')
    'Arr[êe]t[ée]'
    >>> add_accentless_fallbacks(r'foo|bar')
    'foo|bar'
    >>> add_accentless_fallbacks(r'm[êè]me')
    'm[êèe]me'
    >>> add_accentless_fallbacks(r'm[êèe]me')
    'm[êèe]me'
    >>> add_accentless_fallbacks(r'\[Décret')
    '\\[D[ée]cret'
    >>> add_accentless_fallbacks(r'\[(?P<blé>Décret[ée])?(?(blé) à | a )(?P=blé)')
    '\\[(?P<blé>D[ée]cret[ée])?(?(blé) [àa] | a )(?P=blé)'
    >>> add_accentless_fallbacks(r'(?# commenté )')
    '(?# commenté )'
    >>> add_accentless_fallbacks(r'[\]é]')
    '[\\]ée]'
    """
    def remove_accent(c):
        return chr(int(decomposition(c).split(' ', 1)[0], 16))

    r = []
    source = sre_parse.Tokenizer(pattern)
    sourceget = source.get
    while True:
        this = source.next
        if this is None:
            break  # end of pattern
        sourceget()

        if this[0] == '\\':
            r.append(this)
        elif this == '[':
            elements = []
            accented = set()
            while True:
                this = sourceget()
                if this in (None, ']'):
                    break
                elements.append(this)
                if this[0] == '\\':
                    continue
                if decomposition(this):
                    accented.add(this)
            if accented:
                elements_set = set(elements)
                for c in sorted(accented):
                    accentless = remove_accent(c)
                    if accentless not in elements_set:
                        elements.append(accentless)
                        elements_set.add(accentless)
            r.append('[')
            r.extend(elements)
            if this:
                r.append(']')
        elif this == '(' and source.match('?'):
            this = sourceget()
            if this is None:
                this = ''
            elif this == 'P':
                if source.next == '<':
                    # named group
                    this += source.getuntil('>') + '>'
                elif source.next == '=':
                    # named backreference
                    this += source.getuntil(')') + ')'
            elif this == '#':
                # comment
                this += source.getuntil(')') + ')'
            elif this == '(':
                # conditional backreference group
                this += source.getuntil(')') + ')'
            r.append('(?' + this)
        else:
            if decomposition(this):
                this = '[%s%s]' % (this, remove_accent(this))
            r.append(this)

    return ''.join(r)


nonalphanum_re = re.compile(r'[^a-z0-9]')


def strip_accents(s):
    return ''.join(c for c in normalize('NFKD', s) if not combining(c))


strip_down = lambda s: strip_accents(s).lower()


filter_nonalnum = lambda s: nonalphanum_re.sub('', strip_down(s))


def strip_prefix(s, prefix):
    i = len(prefix)
    if s[:i] == prefix:
        return s[i:]
    return s


def id_to_path(i):
    return '/'.join((i[0:4], i[4:8], i[8:10], i[10:12], i[12:14], i[14:16], i[16:18], i))


def reconstruct_path(dossier, cid, sous_dossier, id):
    x = 'en' if dossier.endswith('_en_vigueur') else 'non'
    prefix = 'legi/global/code_et_TNC_%s_vigueur' % x
    if id[4:8] != 'TEXT':
        id = id_to_path(id)
    return '/'.join((prefix, dossier, id_to_path(cid), sous_dossier, id+'.xml'))


def mimic_case(old_word, new_word):
    """
    >>> print(mimic_case('EtAt', 'état'))
    ÉtAt
    """
    if len(old_word) != len(new_word):
        raise ValueError("lengths don't match")
    return ''.join([
        new_word[i].upper() if old_word[i].isupper() else new_word[i].lower()
        for i in range(len(old_word))
    ])


ascii_spaces_re = re.compile(r'(?: {2}| *[\t\n\r\f\v])[ \t\n\r\f\v]*')
nonword_re = re.compile(r'\W', re.U)
spaces_re = re.compile(r'\s+', re.U)
word_re = re.compile(r'\w{2,}', re.U)


def upper_words_percentage(s):
    words = word_re.findall(s)
    if not words:
        return 0
    return len([w for w in words if w.isupper()]) / len(words)


def partition(l, predicate):
    a, b = [], []
    for e in l:
        if predicate(e):
            a.append(e)
        else:
            b.append(e)
    return a, b


def show_match(m, n=30, wrapper='%s{%s}%s'):
    if type(m) is re.Match:
        m_string = m.string
        m_start, m_end = m.span()
    else:
        m_string, (m_start, m_end) = m
    before = max(m_string.rfind(' ', 0, m_start - n), 0) if m_start > n else 0
    before = ('[…]' if before > 0 else '') + m_string[before:m_start]
    after = m_string.find(' ', m_end + n)
    after = m_string[m_end:] if after == -1 else m_string[m_end:after+1] + '[…]'
    return wrapper % (before, m_string[m_start:m_end], after)


def json_serializer(obj):
    if isinstance(obj, date):
        return str(obj)
    raise TypeError("Type %s not serializable" % type(obj))
