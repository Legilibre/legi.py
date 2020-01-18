from collections import namedtuple
from contextlib import contextmanager
from itertools import chain, repeat
import os
import os.path
import re
from sqlite3 import Connection, IntegrityError, OperationalError, ProgrammingError, Row
import sre_parse
import sys
import traceback
from unicodedata import combining, decomposition, normalize


if not hasattr(re, 'Match'):
    # For Python 3.6
    re.Match = type(re.compile('').match(''))


IGNORE = object()
NIL = object()
ROOT = os.path.dirname(__file__) + '/'


@contextmanager
def patch_object(obj, attr, value):
    if value is IGNORE:
        yield
        return
    backup = getattr(obj, attr, NIL)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        if backup is NIL:
            delattr(obj, attr)
        else:
            setattr(obj, attr, backup)


class DB(Connection):
    pass


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def namedtuple_factory(cursor, row):
    return namedtuple('Record', [col[0] for col in cursor.description])(*row)


ROW_FACTORIES = {
    'dict': dict_factory,
    'namedtuple': namedtuple_factory,
    'Row': Row,
}


def connect_db(address, row_factory=None, create_schema=True, update_schema=True, pragmas=()):
    db = DB(address)
    db.address = address
    if row_factory:
        if not callable(row_factory):
            row_factory = ROW_FACTORIES[row_factory]
        db.row_factory = row_factory
    db.insert = inserter(db)
    db.update = updater(db)
    db.run = db.execute

    def all(*a, **kw):
        to_dict = kw.get('to_dict', False)
        with patch_object(db, 'row_factory', dict_factory if to_dict else IGNORE):
            q = db.execute(*a)
        return iter_results(q)

    db.all = all

    def one(*args, **kw):
        to_dict = kw.get('to_dict', False)
        with patch_object(db, 'row_factory', dict_factory if to_dict else IGNORE):
            r = db.execute(*args).fetchone()
            if r and len(r) == 1 and not to_dict:
                r = r[0]
            return r

    db.one = one
    db.changes = lambda: one("SELECT changes()")

    if create_schema:
        try:
            db.run("SELECT 1 FROM db_meta LIMIT 1")
        except OperationalError:
            with open(ROOT + 'sql/schema.sql', 'r') as f:
                db.executescript(f.read())

    if update_schema:
        r = run_migrations(db)
        if r == '!RECREATE!':
            return connect_db(address, row_factory=row_factory, create_schema=True)

    for pragma in pragmas:
        query = "PRAGMA " + pragma
        result = db.one(query)
        print("> Sent `%s` to SQLite, got `%s` as result" % (query, result))

    return db


def inserter(conn):
    def insert(table, attrs, replace=False):
        or_clause = 'OR REPLACE' if replace else ''
        keys, values = zip(*attrs.items())
        keys = ','.join(keys)
        placeholders = ','.join(repeat('?', len(attrs)))
        try:
            conn.execute("""
                INSERT {0} INTO {1} ({2}) VALUES ({3})
            """.format(or_clause, table, keys, placeholders), values)
        except IntegrityError:
            print(table, *attrs.items(), sep='\n    ')
            raise
    return insert


def updater(conn):

    def dict2sql(d, joiner=', '):
        keys, values = zip(*d.items())
        placeholders = joiner.join(k+' = ?' for k in keys)
        return placeholders, values

    def update(table, where, attrs):
        placeholders, values = dict2sql(attrs)
        where_placeholders, where_values = dict2sql(where, joiner=' AND ')
        try:
            conn.execute(
                "UPDATE {0} SET {1} WHERE {2}".format(
                    table, placeholders, where_placeholders
                ),
                values + where_values
            )
        except IntegrityError:
            print(table, *chain(where.items(), attrs.items()), sep='\n    ')
            raise

    return update


def iter_results(q):
    while True:
        r = q.fetchmany()
        if not r:
            return
        for row in r:
            yield row


def run_migrations(db):
    v = db.one("SELECT value FROM db_meta WHERE key = 'schema_version'") or 0
    if v == 0:
        db.insert('db_meta', dict(key='schema_version', value=v))
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
            os.rename(db.address, db.address + '.back')
            return sql
        print('Running DB migration #%s...' % n)
        try:
            db.executescript(sql)
        except (IntegrityError, ProgrammingError):
            traceback.print_exc()
            r = input('Have you already run this migration? (y/N) ')
            if r.lower() != 'y':
                raise SystemExit(1)
        db.run("UPDATE db_meta SET value = ? WHERE key = 'schema_version'", (n,))
        db.commit()
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


class _Tokenizer(sre_parse.Tokenizer):

    if sys.version_info < (3, 8, 0):
        # Prior to Python 3.8 the `getuntil` method didn't have the `name` argument
        def getuntil(self, terminator, name):
            return super(_Tokenizer, self).getuntil(terminator)


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
    source = _Tokenizer(pattern)
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
                    this += source.getuntil('>', 'group name') + '>'
                elif source.next == '=':
                    # named backreference
                    this += source.getuntil(')', 'group name') + ')'
            elif this == '#':
                # comment
                this += source.getuntil(')', 'comment') + ')'
            elif this == '(':
                # conditional backreference group
                this += source.getuntil(')', 'group name') + ')'
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
