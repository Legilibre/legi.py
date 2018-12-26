"""
A spellchecker for French text, based on the `enchant` package.
"""

import re

try:
    from enchant.checker import SpellChecker
    from enchant.tokenize import Filter
except ImportError:
    print("Warning: the `enchant` package is missing, spellchecking won't work")
    SpellChecker = lambda *a, **kw: None
    Filter = object

from .roman import ROMAN_PATTERN_SIMPLE


class RomanNumberFilter(Filter):

    number_re = re.compile(r"^%s$" % ROMAN_PATTERN_SIMPLE)

    def _skip(self, word):
        return bool(self.number_re.match(word))


french_checker = SpellChecker('fr_FR', filters=[RomanNumberFilter])


if french_checker:
    def spellcheck(text):
        french_checker.set_text(text)
        return not list(french_checker)
else:
    def spellcheck(text):
        return
