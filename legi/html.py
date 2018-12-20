"""
This module handles the HTML provided in LEGI.
"""

from argparse import ArgumentParser
from collections import namedtuple
from difflib import ndiff
import json
import re
from xml.parsers import expat

from lxml import etree

try:
    from tqdm import tqdm
except ImportError:
    print('[warning] tqdm is not installed, the progress bar is disabled')
    tqdm = lambda x: x

from .utils import connect_db, group_by_2, ascii_spaces_re


# An immutable type representing the opening of an HTML element
StartTag = namedtuple('StartTag', 'tag void style dropped parent')

# String of ascii whitespace
ASCII_SPACES = ' \t\n\r\f\v'

# Set of HTML block tags
# https://developer.mozilla.org/en-US/docs/Web/HTML/Block-level_elements
BLOCK_ELEMENTS = set('''
    address article aside blockquote canvas dd div dl dt fieldset figcaption
    figure footer form h1 h2 h3 h4 h5 h6 header hgroup hr li main nav noscript
    ol output p pre section table tfoot ul video
'''.split())

# Set of HTML tags around which we want to trim whitespace
TRIM_AROUND_ELEMENTS = BLOCK_ELEMENTS | set('body br td th tr'.split())

# Map of color names to hexadecimal values
COLORS_MAP = {
    'black': '#000000',
    'white': '#ffffff',
}

# Default styles, used to detect redundant attributes
DEFAULT_STYLE = {
    '.collapse-spaces': True,
    'align': 'left',
    'bgcolor': '#ffffff',
    'clear': 'none',
    'color': '#000000',
    'dir': 'ltr',
    'size': '3',  # https://developer.mozilla.org/docs/Web/HTML/Element/font
    'valign': 'baseline',
}

# Set of elements that should not be dropped even if they're completely empty
KEEP_EMPTY = {'body', 'br', 'hr', 'td', 'th'}

# A fake StartTag which holds the default styles
INVISIBLE_ROOT_TAG = StartTag(None, None, DEFAULT_STYLE, True, None)

# Set of attributes that should always be dropped
USELESS_ATTRIBUTES = {'charoff', 'face', 'id'}

# Set of elements that should be dropped if they don't have any attributes
USELESS_WITHOUT_ATTRIBUTES = {'font', 'span'}

# http://w3c.github.io/html/syntax.html#void-elements
# Only two void tags are actually used in LEGI
VOID_ELEMENTS = {'br', 'hr'}


ESCAPE_TABLE = [('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;')]
ESCAPE_ATTR_TABLE = ESCAPE_TABLE + [('"', '&#34;')]


def escape(s, table=ESCAPE_TABLE):
    """Escape &, <, and > in a string of data.
    """
    for c, r in table:
        if c in s:
            s = s.replace(c, r)
    return s


def unescape(s):
    """Unescape &amp;, &lt;, and &gt; in a string of data.
    """
    if '&' not in s:
        return s
    return s.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')


def quoteattr(s, table=ESCAPE_ATTR_TABLE):
    """Escape and quote an attribute value.
    """
    for c, r in table:
        if c in s:
            s = s.replace(c, r)
    return '"%s"' % s


bad_space_re = re.compile(r"[dl]['’] \w| [,.]", re.I | re.U)


def drop_bad_space(m):
    return m.group(0).replace(' ', '')


def is_start_of(s, tag):
    x = tag.__len__()
    return s[0] == '<' and s[1:x+1] == tag and s[x+1] in ' >' and s[-2] != '/'


class HTMLCleaner:
    """A parser target which returns cleaned HTML (as a string, not a tree).

    Doc: http://lxml.de/parsing.html#the-target-parser-interface
    """

    def __init__(self):
        self.at_segment_start = True
        self.drop_line_breaks = True
        self.last_trimmable_node = None
        self.out = []
        self.current_tag = INVISIBLE_ROOT_TAG
        self.text_chunks = []

    def start(self, tag, attrs):
        # Add start tag to stack and output
        void = tag in VOID_ELEMENTS
        attrs_str = ''
        parent = self.current_tag
        parent_styles = parent.style
        new_styles = {}
        if attrs:
            is_list_tag = tag in {'ul', 'ol'}
            for k, v in group_by_2(attrs):
                # Skip useless attributes
                if k in USELESS_ATTRIBUTES:
                    continue
                # Skip obsolete list style attribute
                if is_list_tag and k == 'type':
                    continue
                # Normalize the value
                v = v.strip()
                if k[-5:] == 'color':
                    v = v.lower()
                    if v[:4] == 'rgb(':
                        v = '#%02x%02x%02x' % tuple(int(s.strip()) for s in v[4:-1].split(','))
                    elif v.__len__() == 6 and v.isdigit():
                        v = '#' + v
                    else:
                        v = COLORS_MAP.get(v, v)
                # Skip redundant styles
                parent_style = parent_styles.get(k)
                if parent_style == v:
                    continue
                if parent_style:
                    if k == 'size':
                        size = int(v)
                        # Skip 0 (invalid) and 4 through 7 (enlarged text)
                        if size == 0 or size > 3:
                            continue
                    new_styles[k] = v
                # Add to output
                attrs_str += ' %s=%s' % (k, quoteattr(v))
        if tag == 'pre':
            new_styles['.collapse-spaces'] = False
        styles = dict(parent_styles, **new_styles) if new_styles else parent_styles
        if self.drop_line_breaks and ''.join(self.text_chunks).strip(ASCII_SPACES):
            self.drop_line_breaks = False
        dropped = (
            not attrs_str and tag in USELESS_WITHOUT_ATTRIBUTES or
            tag == 'br' and self.drop_line_breaks
        )
        start_tag = StartTag(tag, void, styles, dropped, parent)
        if not dropped:
            # Process queued text chunks
            if self.text_chunks:
                self.handle_text(next_tag=start_tag)
            # Add start tag to output
            self.out.append('<' + tag + attrs_str + ('/>' if void else '>'))
        self.current_tag = start_tag

    def end(self, tag):
        start_tag = self.current_tag
        # Don't add an end tag if the start tag was self-closed or skipped
        if start_tag.void or start_tag.dropped:
            self.current_tag = start_tag.parent
            return
        # Clean up empty elements
        collapsed = False
        if is_start_of(self.out[-1], tag):
            if not ''.join(self.text_chunks).strip(ASCII_SPACES):
                tag_has_attributes = self.out[-1].__len__() > tag.__len__() + 2
                if tag_has_attributes or tag in KEEP_EMPTY:
                    # Drop the whitespace chunks, if any
                    self.text_chunks = []
                    # Collapse the element
                    self.out[-1] = self.out[-1][:-1] + '/>'
                    collapsed = True
                else:
                    # Drop the element entirely
                    self.out.pop()
                    if self.out and self.out[-1][0] != '<':
                        # Previous output element was a text node, put it back
                        # in the chunks queue
                        self.text_chunks.insert(0, unescape(self.out.pop()))
                        # Reset last_trimmable_node (we don't need to restore
                        # its previous value)
                        self.last_trimmable_node = None
                    self.current_tag = start_tag.parent
                    return
        # Process queued text chunks
        if self.text_chunks:
            self.handle_text()
        # Handle whitespace collapsing
        if tag in TRIM_AROUND_ELEMENTS:
            # Drop tail space
            if self.last_trimmable_node:
                i, self.last_trimmable_node = self.last_trimmable_node, None
                self.out[i] = self.out[i][:-1]
            # Enable dropping the next space
            self.at_segment_start = True
        # Update current_tag
        self.current_tag = start_tag.parent
        # Add end tag to output
        if not collapsed:
            self.out.append('</%s>' % tag)

    def data(self, text):
        # We can't always get a single string for a text node, so we store
        # chunks in a list and assemble them when we're ready
        self.text_chunks.append(text)

    def handle_text(self, next_tag=None):
        text = ''.join(self.text_chunks)
        self.text_chunks = []
        if not text:
            return
        # Collapse spaces, unless we're inside a <pre>
        # https://www.w3.org/TR/css-text-3/#white-space-processing
        if self.current_tag.style['.collapse-spaces']:
            text = ascii_spaces_re.sub(' ', text)
            # Handle spaces around closing tags
            i = self.last_trimmable_node
            if i and not next_tag and self.out[i - 1][:2] == '</':
                # `</i> foo </b>bar` → `</i> foo</b> bar`
                trimmed = self.out[i][:-1]
                if trimmed:
                    self.out[i] = trimmed
                else:
                    self.out.pop(i)
                i = self.last_trimmable_node = None
                if text[0] != ' ':
                    text = ' ' + text
            # Drop leading space if the previous text node has a trailing space
            # or if we're at the beginning of a "segment"
            if text[0] == ' ' and (self.last_trimmable_node or self.at_segment_start):
                text = text[1:]
                if not text:
                    return
            # French-specific dropping of bad spaces, e.g. "l' article" → "l'article"
            text = bad_space_re.sub(drop_bad_space, text)
            # Are we about to open a new non-inline element?
            if next_tag and next_tag.tag in TRIM_AROUND_ELEMENTS:
                self.at_segment_start = True
                # Drop tail space
                if text[-1] == ' ':
                    text = text[:-1]
                    if not text:
                        return
            else:
                self.at_segment_start = False
            # Does the trimmable text node we're adding have a tail space?
            if text[-1] == ' ':
                self.last_trimmable_node = self.out.__len__()
            else:
                self.last_trimmable_node = None
        else:
            self.last_trimmable_node = None
        # Stop dropping <br> tags
        if self.drop_line_breaks:
            self.drop_line_breaks = False
        # Add to output
        self.out.append(escape(text))

    def close(self):
        if self.text_chunks:
            self.out.append(''.join(self.text_chunks).rstrip(ASCII_SPACES))
        # Join the output into a single string, then reset the parser before
        # returning so that it can be reused
        r = ''.join(self.out)
        self.__init__()
        return r


def clean_html(html, cleaner=HTMLCleaner()):
    """Returns cleaned HTML

    Warning: this function is not thread safe unless you provide your own
    thread-local `cleaner` instance.
    """
    p = expat.ParserCreate()
    p.buffer_text = True
    p.ordered_attributes = True
    p.StartElementHandler = cleaner.start
    p.EndElementHandler = cleaner.end
    p.CharacterDataHandler = cleaner.data
    p.Parse('<body>')
    p.Parse(html)
    p.Parse('</body>', 1)
    return cleaner.close()[6:-7]


first_paragraph_re = re.compile(r"^(?:<p(?: [^>]+)?>(.+?)</p>|(.+?)<br/><br/>)(.*)")


def split_first_paragraph(html):
    r"""Extract the content of the first paragraph from an HTML snippet.

    Returns a two-tuple `(first_paragraph, rest)`.

    >>> split_first_paragraph('<br/><p align="center">Foobar</p>')
    ('Foobar', '')
    >>> split_first_paragraph('First line<br/>Second line<br/><br/><p>Lorem <b>ipsum</b></p>')
    ('First line\nSecond line', '<p>Lorem <b>ipsum</b></p>')
    """
    m = first_paragraph_re.match(clean_html(html))
    if m:
        return (m.group(1) or m.group(2)).replace('<br/>', '\n').strip(), m.group(3)
    return '', ''


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
            delta = html_c.__len__() - html.__len__()
            stats['delta'] += delta
            if not check:
                continue
            # Check lengths
            if delta > 0:
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


class StatsCollector:
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
    p.add_argument('--font-size', default='keep-small', choices=['drop', 'keep-small', 'preserve'],
                   help="what to do with the `size` attribute of `font` elements")
    p.add_argument('--skip-checks', default=False, action='store_true',
                   help="skips checking the result of HTML cleaning")
    args = p.parse_args()

    if args.font_size == 'drop':
        USELESS_ATTRIBUTES.add('size')
    elif args.font_size == 'preserve':
        DEFAULT_STYLE.pop('size')

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
