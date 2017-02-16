# encoding: utf8

from __future__ import division, print_function, unicode_literals

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from collections import namedtuple
from contextlib import contextmanager
from itertools import chain, repeat
import os.path
import re
from sqlite3 import Connection, IntegrityError, OperationalError, ProgrammingError, Row
import traceback
from unicodedata import combining, normalize


input = getattr(builtins, 'raw_input', input)


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


def connect_db(address, row_factory=None, create_schema=True, update_schema=True):
    db = DB(address)
    if row_factory:
        if not callable(row_factory):
            row_factory = ROW_FACTORIES[row_factory]
        db.row_factory = row_factory
    db.all = lambda *a: iter_results(db.execute(*a))
    db.insert = inserter(db)
    db.update = updater(db)
    db.run = db.execute

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
        run_migrations(db)

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


nonalphanum_re = re.compile(r'[^a-z0-9]')


_unicode = getattr(builtins, 'unicode', str)


def strip_accents(s):
    return ''.join(c for c in normalize('NFKD', _unicode(s)) if not combining(c))


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


nonword_re = re.compile(r'\W', re.U)
spaces_re = re.compile(r'\s+', re.U)
word_re = re.compile(r'\w{2,}', re.U)


def upper_words_percentage(s):
    words = word_re.findall(s)
    return len([w for w in words if w.isupper()]) / len(words)
