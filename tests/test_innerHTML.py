from lxml import etree

from dila2sql.importer.process_xml import innerHTML


def test_innerHTML():
    el = etree.fromstring('<root></root>')
    assert innerHTML(el) == ''
    el = etree.fromstring('<root>text</root> ')
    assert innerHTML(el) == 'text'
    el = etree.fromstring('<root >text</root>')
    assert innerHTML(el) == 'text'
    el = etree.fromstring('<root attr="value"> </root>')
    assert innerHTML(el) == ' '
