# coding: utf8
from __future__ import division, print_function, unicode_literals

from lxml import etree

from legi.tar2sqlite import innerHTML


def test_innerHTML():
    el = etree.fromstring('<root></root>')
    assert innerHTML(el) == ''
    el = etree.fromstring('<root>text</root> ')
    assert innerHTML(el) == 'text'
    el = etree.fromstring('<root >text</root>')
    assert innerHTML(el) == 'text'
    el = etree.fromstring('<root attr="value"> </root>')
    assert innerHTML(el) == ' '
