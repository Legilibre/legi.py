# encoding: utf8

# This file is part of a program licensed under the terms of the GNU
# General Public License version 3 (or at your option any later version)
# as published by the Free Software Foundation: http://www.gnu.org/licenses/


from __future__ import division, print_function, unicode_literals

import __builtin__
from itertools import chain, repeat
import re
from sqlite3 import Connection, IntegrityError
from unicodedata import combining, normalize


input = getattr(__builtin__, 'raw_input', input)


class DB(Connection): pass


def connect_db(address):
    db = DB(address)
    db.all = lambda *a: iter_results(db.execute(*a))
    db.insert = inserter(db)
    db.update = updater(db)
    db.run = db.execute

    def one(*args):
        r = db.execute(*args).fetchone()
        if r and len(r) == 1:
            return r[0]
        return r

    db.one = one
    db.changes = lambda: one("SELECT changes()")

    return db


def inserter(conn):
    def insert(table, attrs):
        keys, values = zip(*attrs.items())
        keys = ','.join(keys)
        placeholders = ','.join(repeat('?', len(attrs)))
        try:
            conn.execute("""
                INSERT INTO {0} ({1}) VALUES ({2})
            """.format(table, keys, placeholders), values)
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
