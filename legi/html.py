# encoding: utf8

"""
This module handles the HTML provided in LEGI.
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from collections import namedtuple
from difflib import ndiff
import json
import re
from xml.parsers import expat
from xml.sax.saxutils import escape, quoteattr

from lxml import etree
from maps import FrozenMap

try:
    from tqdm import tqdm
except ImportError:
    print('[warning] tqdm is not installed, the progress bar is disabled')
    tqdm = lambda x: x

from .utils import connect_db, group_by_2, input, spaces_re


# An immutable type representing the opening of an HTML element
StartTag = namedtuple('StartTag', 'tag void style dropped')

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
        self.text_chunks = []

    def start(self, tag, attrs):
        if self.text_chunks:
            self.handle_text()
        # Add start tag to stack and output
        void = tag in VOID_ELEMENTS
        attrs_str = ''
        parent_styles = self.tag_stack[-1].style
        new_styles = {}
        for k, v in group_by_2(attrs):
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
            attrs_str += ' %s=%s' % (k, quoteattr(v))
        if tag == 'pre':
            new_styles['.collapse-spaces'] = False
        styles = FrozenMap(parent_styles, **new_styles) if new_styles else parent_styles
        dropped = (
            not attrs_str and tag in USELESS_WITHOUT_ATTRIBUTES or
            len(self.out) == 1 and tag == 'br'
        )
        self.tag_stack.append(StartTag(tag, void, styles, dropped))
        if not dropped:
            self.out.append('<' + tag + attrs_str + (' />' if void else '>'))

    def end(self, tag):
        if self.text_chunks:
            self.handle_text()
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
        # We can't rely on the parser to give us a single string for each text
        # node, so we assemble the chunks ourselves
        self.text_chunks.append(text)

    def handle_text(self):
        text = ''.join(self.text_chunks)
        self.text_chunks = []
        if not text.strip():
            return
        # Collapse spaces, unless we're inside a <pre>
        # https://www.w3.org/TR/css-text-3/#white-space-processing
        if self.tag_stack[-1].style['.collapse-spaces']:
            text = spaces_re.sub(' ', text)
            # French-specific dropping of bad spaces, e.g. "l' article" → "l'article"
            text = bad_space_re.sub(drop_bad_space, text)
        # Add to output
        self.out.append(escape(text))

    def close(self):
        if self.text_chunks:
            self.handle_text()
        # Join the output into a single string, then reset the parser before
        # returning so that it can be reused
        r = ''.join(self.out).rstrip()
        self.__init__()
        return r


def clean_html(html):
    """Returns cleaned HTML

    This function is a simple wrapper around the HTMLCleaner class.
    """
    cleaner = HTMLCleaner()
    p = expat.ParserCreate()
    p.buffer_text = True
    p.ordered_attributes = True
    p.StartElementHandler = cleaner.start
    p.EndElementHandler = cleaner.end
    p.CharacterDataHandler = cleaner.data
    p.Parse('<root>')
    p.Parse(html)
    p.Parse('</root>', 1)
    return cleaner.close()[6:-7]


strip_re = re.compile(r"<.+?>|[ \t\n\r\f\v]+", re.S)


def clean_all_html_in_db(db, check=True):
    stats = {'cleaned': 0, 'delta': 0, 'total': 0}

    def clean_row(table, row):
        row_id = row.pop('id')
        update = {}
        for col, html in row.items():
            stats['total'] += 1
            if not html:
                continue
            html_c = clean_html(html)
            if html_c == html:
                continue
            update[col] = html_c
            stats['cleaned'] += 1
            stats['delta'] += len(html_c) - len(html)
            if not check:
                continue
            # Check lengths
            if len(html_c) > len(html):
                print()
                print("=" * 70)
                print((
                    "Warning: cleaning column '%s' of row '%s' increased the "
                    "length from %i to %i. Diff:"
                ) % (col, row_id, len(html), len(html_c)))
                print(diff_html(html, html_c))
            # Check that no meaningfull text content was lost
            html_s, html_c_s = strip_re.sub('', html), strip_re.sub('', html_c)
            if html_s != html_c_s:
                print()
                print("=" * 70)
                print("Cleaning column '%s' of row '%s' resulted in content loss. Diff:" %
                      (col, row_id))
                print(*ndiff([html_s], [html_c_s], None, None), sep='\n')
            # Check that cleaning a second time does not alter the result
            try:
                html_c_2 = clean_html(html_c)
            except Exception:
                print()
                print("Cleaning a second time failed for column '%s' of row '%s'. Diff:" %
                      (col, row_id))
                print(diff_html(html, html_c))
                raise
            if html_c_2 != html_c:
                print()
                print("=" * 70)
                print("Inconsistent output for column '%s' of row '%s'." % (col, row_id))
                print("*" * 5, "Original data:", "*" * 5)
                print(html)
                print("*" * 5, "Second run diff:", "*" * 5)
                print(diff_html(html_c, html_c_2))
        if update:
            db.update(table, dict(id=row_id), update)

    # Articles
    print("Cleaning articles...")
    q = db.all("SELECT id, bloc_textuel, nota FROM articles", to_dict=True)
    for row in tqdm(q):
        clean_row('articles', row)
    # Textes
    print("Cleaning textes_versions...")
    q = db.all("""
        SELECT id, visas, signataires, tp, nota, abro, rect
          FROM textes_versions
    """, to_dict=True)
    for row in tqdm(q):
        clean_row('textes_versions', row)

    # Print stats
    print("Done.")
    print("Cleaned %(cleaned)i HTML fragments, out of %(total)i. Char delta = %(delta)i." % stats)


def split_html_into_lines(html):
    """Splits an HTML document into lines based on element boundaries.
    """
    tags = '(?:%s)' % ('|'.join(TRIM_AROUND_ELEMENTS))
    html_split_re = re.compile(r"</{0}>".format(tags), re.I)
    return html_split_re.sub('\\0\n', html.replace('\n', '\\n')).split('\n')


def diff_html(html_a, html_b):
    """Diff two HTML documents.
    """
    a, b = split_html_into_lines(html_a), split_html_into_lines(html_b)
    return '\n'.join(ndiff(a, b, None, None))


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


def analyze(db):
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
    p.add_argument('command', choices=['analyze', 'clean'])
    p.add_argument('db')
    p.add_argument('--skip-checks', default=False, action='store_true',
                   help="skips checking the result of HTML cleaning")
    args = p.parse_args()

    db = connect_db(args.db)
    try:
        with db:
            if args.command == 'analyze':
                analyze(db)
            elif args.command == 'clean':
                clean_all_html_in_db(db, check=(not args.skip_checks))
                save = input('Save changes? (y/N) ')
                if save.lower() != 'y':
                    raise KeyboardInterrupt
                db.insert('db_meta', dict(key='raw', value=False), replace=True)
    except KeyboardInterrupt:
        pass
