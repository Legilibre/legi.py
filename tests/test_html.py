# coding: utf8
from __future__ import division, print_function, unicode_literals

from legi.html import clean_html


def test_clean_html_drops_empty_elements_and_text_nodes():
    unclean = '''
        <p>Lorem ipsum</p>
        <p> <pre> </pre> </p>
    '''
    cleaned = clean_html(unclean)
    expected = '<p>Lorem ipsum</p>'
    assert cleaned == expected


def test_clean_html_drops_useless_attributes_and_elements():
    unclean = '''
        <h1 align="center">Titre <font>1</font></h1>
        <p id="foo"><span align="left"></span></p>
    '''
    cleaned = clean_html(unclean)
    expected = '<h1 align="center">Titre 1</h1>'
    assert cleaned == expected


def test_clean_html_does_not_alter_clean_html():
    expected = '<h1 align="center">Titre</h1><p>Lorem ipsum</p>'
    actual = clean_html(expected)
    assert actual == expected


def test_clean_html_does_not_collapse_spaces_inside_pre():
    unclean = '''
        <pre>    print("Hello world")
        </pre>
    '''
    actual = clean_html(unclean)
    expected = unclean.strip()
    assert actual == expected
