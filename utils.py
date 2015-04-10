# encoding: utf8
from __future__ import division, print_function, unicode_literals

from itertools import repeat
import re
from sqlite3 import IntegrityError
from unicodedata import combining, normalize


input = __builtins__.get('raw_input', input)


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
