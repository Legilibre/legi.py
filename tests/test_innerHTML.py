from lxml import etree

from dila2sql.importer import innerHTML


def test_innerHTML():
    el = etree.fromstring('<root></root>')
    assert innerHTML(el) == ''
    el = etree.fromstring('<root>text</root> ')
    assert innerHTML(el) == 'text'
    el = etree.fromstring('<root >text</root>')
    assert innerHTML(el) == 'text'
    el = etree.fromstring('<root attr="value"> </root>')
    assert innerHTML(el) == ' '
