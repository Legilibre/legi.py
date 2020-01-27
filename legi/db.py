"""
This module provides tools to interact with SQLite databases.
"""

from collections import deque
from itertools import chain, repeat
import os
from sqlite3 import Connection, IntegrityError, OperationalError, ProgrammingError, Row
import traceback
import warnings

from .utils import patch_object, IGNORE, ROOT


class DB(Connection):
    __slots__ = ('address', 'warning_threshold')

    def __init__(self, address, row_factory=None, warning_threshold=100, autocommit=True):
        Connection.__init__(self, address)
        self.address = address
        if autocommit:
            self.isolation_level = None
        if row_factory:
            if not callable(row_factory):
                row_factory = ROW_FACTORIES[row_factory]
            self.row_factory = row_factory
        self.warning_threshold = warning_threshold

    def all(self, *a, to_dict=False):
        """This method queries the DB and yields the rows one by one.
        """
        if to_dict:
            with patch_object(self, 'row_factory', dict_factory):
                cursor = self.execute(*a)
        else:
            cursor = self.execute(*a)
        fetchone = cursor.fetchone
        row = fetchone()
        if not row:
            return
        if not to_dict and row.__len__() == 1:
            while row:
                yield row[0]
                row = fetchone()
        else:
            while row:
                yield row
                row = fetchone()

    def deque(self, *a, to_dict=False):
        """This method queries the DB and returns all the rows as a deque.
        """
        return deque(self.all(*a, to_dict=to_dict))

    def list(self, *a, to_dict=False):
        """This method queries the DB and returns all the rows as a list.
        """
        if to_dict:
            with patch_object(self, 'row_factory', dict_factory):
                cursor = self.execute(*a)
        else:
            cursor = self.execute(*a)
        rows = cursor.fetchall()
        if rows:
            if rows.__len__() > self.warning_threshold:
                warnings.warn((
                    "The query returned a lot of rows (%i), you should probably use "
                    "the .all() method to iterate over the results instead of "
                    "loading them all as one big list."
                ) % rows.__len__(), ResourceWarning, stacklevel=2)
            if not to_dict and rows[0].__len__() == 1:
                return [row[0] for row in rows]
        return rows

    def one(self, *args, to_dict=False):
        """This method queries the DB and returns a single row.
        """
        with patch_object(self, 'row_factory', dict_factory if to_dict else IGNORE):
            r = self.execute(*args).fetchone()
            if r and not to_dict and r.__len__() == 1:
                r = r[0]
            return r

    def changes(self):
        """This method returns the result of `SELECT changes()`.
        """
        return self.one("SELECT changes()")

    def insert(self, table, attrs, replace=False):
        """This method inserts one row into the DB.
        """
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
        """This method updates one row in the DB.
        """
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


class Record(Row):
    """This row type allows accessing columns as attributes.
    """

    def __getattr__(self, col):
        try:
            return self[col]
        except KeyError:
            raise AttributeError(col)

    def __repr__(self):
        return 'Record(' + ', '.join(
            '='.join((col, repr(self[col]))) for col in self.keys()
        ) + ')'


ROW_FACTORIES = {
    'dict': dict_factory,
    'Record': Record,
    'Row': Row,
}


def connect_db(
    address, row_factory=None, create_schema=True, update_schema=True,
    pragmas=(), autocommit=True,
):
    db = DB(address, row_factory=row_factory, autocommit=autocommit)

    if create_schema:
        try:
            db.run("SELECT 1 FROM db_meta LIMIT 1")
        except OperationalError:
            with open(ROOT + 'sql/schema.sql', 'r') as f:
                db.executescript(f.read())

    if update_schema:
        r = run_migrations(db)
        if r == '!RECREATE!':
            return connect_db(
                address, row_factory=row_factory, create_schema=True,
                pragmas=pragmas, autocommit=autocommit,
            )

    for pragma in pragmas:
        query = "PRAGMA " + pragma
        result = db.one(query)
        print("> Sent `%s` to SQLite, got `%s` as result" % (query, result))

    return db


def run_migrations(db):
    v = db.one("SELECT value FROM db_meta WHERE key = 'schema_version'") or 0
    if v == 0:
        db.insert('db_meta', dict(key='schema_version', value=v))
    with open(ROOT + 'sql/migrations.sql') as f:
        migrations = f.read().split('\n\n-- migration #')
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
