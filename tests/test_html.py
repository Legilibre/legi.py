from legi.html_utils import clean_html


def test_clean_html_on_empty_string():
    r = clean_html('')
    assert r == ''


def test_clean_html_on_single_whitespace():
    r = clean_html(' ')
    assert r == ''


def test_clean_html_collapses_spaces():
    unclean = '<s> Lorem \r <b><i> ipsum</i> dolor\n\t</b>sit </s>'
    cleaned = clean_html(unclean)
    expected = '<s>Lorem <b><i>ipsum</i> dolor</b> sit</s>'
    assert cleaned == expected


def test_clean_html_drops_spaces_around_line_breaks():
    # Basic
    unclean = '<p>\t Lorem ipsum\n </p>'
    cleaned = clean_html(unclean)
    expected = '<p>Lorem ipsum</p>'
    assert cleaned == expected
    # Complex
    unclean = '<p> <i> \nLorem <br/> ipsum\n </i> </p>'
    cleaned = clean_html(unclean)
    expected = '<p><i>Lorem<br/>ipsum</i></p>'
    assert cleaned == expected


def test_clean_html_drops_bad_spaces():
    unclean = "L' <span>article 2</span>\n."
    cleaned = clean_html(unclean)
    expected = "L'article 2."
    assert cleaned == expected


def test_clean_html_drops_empty_elements_and_text_nodes():
    unclean = '''
        <p>Lorem ipsum</p>
        <p> <pre> </pre> </p>
    '''
    cleaned = clean_html(unclean)
    expected = '<p>Lorem ipsum</p>'
    assert cleaned == expected


def test_clean_html_drops_line_breaks_at_the_beginning():
    unclean = ' <br/> <p> <br/> <br/> Text</p>'
    cleaned = clean_html(unclean)
    expected = '<p>Text</p>'
    assert cleaned == expected


def test_clean_html_does_not_drop_empty_table_cells():
    unclean = '<tr><th></th><td> </td></tr><tr> </tr>'
    cleaned = clean_html(unclean)
    expected = '<tr><th/><td/></tr>'
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
    expected = '<h1 align="center">Titre</h1><p>Lorem ipsum &amp;</p>'
    actual = clean_html(expected)
    assert actual == expected


def test_clean_html_does_not_collapse_spaces_inside_pre():
    unclean = '''
        <pre>    print("&gt; Hello world")
        </pre>
    '''
    actual = clean_html(unclean)
    expected = unclean.strip()
    assert actual == expected


def test_clean_html_escapes_properly():
    original = '<p attr="&quot;">&lt;p&gt;</p>'
    actual = clean_html(original)
    expected = '''<p attr="&#34;">&lt;p&gt;</p>'''
    assert actual == expected


def test_clean_html_preserves_attribute_order():
    expected = '<h1 a="0" b="1" c="2" d="3" e="4">Titre</h1>'
    actual = clean_html(expected)
    assert actual == expected
