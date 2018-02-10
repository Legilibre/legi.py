# encoding: utf8

"""
This module handles the HTML provided in LEGI.
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
import json

from lxml import etree

from .utils import connect_db


class StatsCollector(object):
    """Collects stats about the HTML tags and attributes used in LEGI
    """

    def __init__(self):
        self.stats = {}

    def start(self, tag, attrs):
        try:
            tag_stats = self.stats[tag]
        except KeyError:
            tag_stats = self.stats[tag] = {'count': 0, 'attrs': {}}
        tag_stats['count'] += 1
        tag_stats_attrs = tag_stats['attrs']
        for attr in attrs.items():
            if attr[0] == 'id':
                attr = attr[0]
            elif attr[1].lstrip('-').isdigit():
                attr = "%s = <integer>" % attr[0]
            elif attr[1][-1:] == '%' and attr[1][:-1].isdigit():
                attr = "%s = <percentage>" % attr[0]
            else:
                attr = "%s = %s" % attr
            try:
                tag_stats_attrs[attr] += 1
            except KeyError:
                tag_stats_attrs[attr] = 1

    def comment(self):
        self.start('<!--', ())

    def close(self):
        r = self.stats
        self.__init__()
        return r


def main(db):
    parser = etree.XMLParser(target=StatsCollector())
    parser.feed('<root>')
    # Articles
    q = db.all("""
        SELECT id, bloc_textuel, nota
          FROM articles
    """)
    for article_id, bloc_textuel, nota in q:
        if bloc_textuel:
            parser.feed(bloc_textuel)
        if nota:
            parser.feed(nota)
    # Textes
    q = db.all("""
        SELECT id, visas, signataires, tp, nota, abro, rect
          FROM textes_versions
    """)
    for row in q:
        for text in row[1:]:
            if text:
                parser.feed(text)
    # Result
    parser.feed('</root>')
    stats = parser.close()
    if stats['root']['count'] == 1:
        del stats['root']
    else:
        stats['root']['count'] -= 1
    print(json.dumps(stats, indent=4, sort_keys=True))


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    args = p.parse_args()

    db = connect_db(args.db)
    try:
        main(db)
    except KeyboardInterrupt:
        pass
