# encoding: utf8

"""
This module handles the HTML provided in LEGI.
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from cgi import escape
import json
import re

from lxml import etree
from maps import FrozenMap, namedfrozen

from .utils import connect_db, spaces_re


# An immutable type representing the opening of an HTML element
StartTag = namedfrozen(str('StartTag'), ['tag', 'void', 'style', 'dropped'])

# Map of color names to hexadecimal values
COLORS_MAP = {
    'black': '#000000',
    'white': '#ffffff',
}

# Default styles, used to detect redundant attributes
DEFAULT_STYLE = FrozenMap({
    '.collapse-spaces': True,
    'align': 'left',
    'bgcolor': '#ffffff',
    'clear': 'none',
    'color': '#000000',
    'dir': 'ltr',
    'valign': 'baseline',
})

# Set of elements that should not be dropped even if they're completely empty
KEEP_EMPTY = {'td', 'th'}

# A fake StartTag which holds the default styles
INVISIBLE_ROOT_TAG = StartTag(None, None, DEFAULT_STYLE, True)

# Set of attributes that should always be dropped
USELESS_ATTRIBUTES = {'charoff', 'id'}

# Set of elements that should be dropped if they don't have any attributes
USELESS_WITHOUT_ATTRIBUTES = {'font', 'span'}

# http://w3c.github.io/html/syntax.html#void-elements
# Only two void tags are actually used in LEGI
VOID_ELEMENTS = {'br', 'hr'}


bad_space_re = re.compile(r"[dl]['’] \w| [,.]", re.U)


def drop_bad_space(m):
    return m.group(0).replace(' ', '')


class HTMLCleaner(object):
    """A parser target which returns cleaned HTML (as a string, not a tree).

    Doc: http://lxml.de/parsing.html#the-target-parser-interface
    """

    def __init__(self):
        self.out = []
        self.tag_stack = [INVISIBLE_ROOT_TAG]

    def start(self, tag, attrs):
        # Add start tag to stack and output
        void = tag in VOID_ELEMENTS
        attrs_str = ''
        parent_styles = self.tag_stack[-1].style
        new_styles = {}
        for k, v in attrs.items():
            # Skip useless attributes
            if k in USELESS_ATTRIBUTES:
                continue
            # Skip obsolete list style attribute
            if k == 'type' and tag in {'ul', 'ol'}:
                continue
            # Normalize the value
            v = v.strip()
            if k.endswith('color'):
                v = v.lower()
                if v.startswith('rgb('):
                    v = '#%02x%02x%02x' % tuple(int(s.strip()) for s in v[4:-1].split(','))
                elif len(v) == 6 and v.isdigit():
                    v = '#' + v
                else:
                    v = COLORS_MAP.get(v, v)
            # Skip redundant styles
            parent_style = parent_styles.get(k)
            if parent_style == v:
                continue
            if parent_style:
                new_styles[k] = v
            # Add to output
            attrs_str += ' %s="%s"' % (k, escape(v))
        if tag == 'pre':
            new_styles['.collapse-spaces'] = False
        styles = FrozenMap(parent_styles, **new_styles) if new_styles else parent_styles
        dropped = not attrs_str and tag in USELESS_WITHOUT_ATTRIBUTES
        self.tag_stack.append(StartTag(tag, void, styles, dropped))
        if not dropped:
            self.out.append('<' + tag + attrs_str + (' />' if void else '>'))

    def end(self, tag):
        start_tag = self.tag_stack.pop()
        # Don't add an end tag if the start tag was self-closed or skipped
        if start_tag.void or start_tag.dropped:
            return
        # Drop empty elements, unless they're in the KEEP_EMPTY set
        if tag not in KEEP_EMPTY and self.out[-1] == '<%s>' % tag:
            self.out.pop()
            return
        # Add end tag to output
        self.out.append('</%s>' % tag)

    def data(self, text):
        # Skip if it's all whitespace
        if not text.strip():
            return
        # Collapse spaces, unless we're inside a <pre>
        # https://www.w3.org/TR/css-text-3/#white-space-processing
        if self.tag_stack[-1].style['.collapse-spaces']:
            text = spaces_re.sub(' ', text)
            # French-specific dropping of bad spaces, e.g. "l' article" → "l'article"
            text = bad_space_re.sub(drop_bad_space, text)
        # Add to output
        self.out.append(text)

    def close(self):
        # Join the output into a single string, then reset the parser before
        # returning so that it can be reused
        r = ''.join(self.out).rstrip()
        self.__init__()
        return r


cleaner = etree.XMLParser(target=HTMLCleaner())


def clean_html(html):
    """Returns cleaned HTML

    This function is a simple wrapper around the HTMLCleaner class.
    """
    cleaner.feed('<root>')
    cleaner.feed(html)
    cleaner.feed('</root>')
    return cleaner.close()[6:-7]


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
