"""
This module provides tools to interact with SQLite databases.
"""

from itertools import chain, repeat
import os
from sqlite3 import Connection, IntegrityError, OperationalError, ProgrammingError, Row
import traceback

from .utils import patch_object, IGNORE, ROOT


class DB(Connection):

    def __init__(self, address, row_factory=None):
        Connection.__init__(self, address)
        self.address = address
        if row_factory:
            if not callable(row_factory):
                row_factory = ROW_FACTORIES[row_factory]
            self.row_factory = row_factory

    def all(self, *a, **kw):
        to_dict = kw.get('to_dict', False)
        with patch_object(self, 'row_factory', dict_factory if to_dict else IGNORE):
            q = self.execute(*a)
        return iter_results(q)

    def one(self, *args, **kw):
        to_dict = kw.get('to_dict', False)
        with patch_object(self, 'row_factory', dict_factory if to_dict else IGNORE):
            r = self.execute(*args).fetchone()
            if r and len(r) == 1 and not to_dict:
                r = r[0]
            return r

    def changes(self):
        return self.one("SELECT changes()")

    def insert(self, table, attrs, replace=False):
        or_clause = 'OR REPLACE' if replace else ''
        keys, values = zip(*attrs.items())
        keys = ','.join(keys)
        placeholders = ','.join(repeat('?', len(attrs)))
        try:
            self.execute(
                f"INSERT {or_clause} INTO {table} ({keys}) VALUES ({placeholders})",
                values
            )
        except IntegrityError:
            print(table, *attrs.items(), sep='\n    ')
            raise

    def update(self, table, where, attrs):
        placeholders, values = dict2sql(attrs)
        where_placeholders, where_values = dict2sql(where, joiner=' AND ')
        try:
            self.execute(
                f"UPDATE {table} SET {placeholders} WHERE {where_placeholders}",
                values + where_values
            )
        except IntegrityError:
            print(table, *chain(where.items(), attrs.items()), sep='\n    ')
            raise

    run = Connection.execute


def dict2sql(d, joiner=', '):
    keys, values = zip(*d.items())
    placeholders = joiner.join(k+' = ?' for k in keys)
    return placeholders, values


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class Record:
    __slots__ = ('_cols', '_vals')

    def __init__(self, cols, values):
        self._cols = {col: i for i, col in enumerate(cols)}
        self._vals = values

    def __getitem__(self, key):
        return self._vals[key if type(key) is int else self._cols[key]]

    def __getattr__(self, col):
        try:
            return self._vals[self._cols[col]]
        except KeyError:
            raise AttributeError(col)

    def __len__(self):
        return len(self._vals)

    def __repr__(self):
        return ''.join('Record(', (
            ', '.join(
                '='.join(
                    (col, repr(self._vals[i]))
                    for col, i in self._cols
                )
            )
        ), ')')


def record_factory(cursor, row):
    return Record((col[0] for col in cursor.description), row)


ROW_FACTORIES = {
    'dict': dict_factory,
    'Record': record_factory,
    'Row': Row,
}


def connect_db(address, row_factory=None, create_schema=True, update_schema=True, pragmas=()):
    db = DB(address, row_factory=row_factory)

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
