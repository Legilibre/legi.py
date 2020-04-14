"""
Spellchecking based on the `hunspell` library.
"""

import os
import re

from appdirs import site_data_dir

from .roman import ROMAN_PATTERN_SIMPLE


APOSTROPHES = "'’"
HYPHENS = "-‐‑"
INTRA_WORD_CHARS = APOSTROPHES + HYPHENS + "."  # the dot is for abbreviations


class SpellcheckingIsUnavailable(Exception):
    pass


class Spellchecker:
    """A thread-safe spellchecker for a specific language.
    """
    __slots__ = ('lang', 'dict', 'filters', 'intra_word_chars')

    def __init__(self, lang, filters=(), intra_word_chars=INTRA_WORD_CHARS):
        self.lang = lang
        try:
            import hunspell
        except ImportError:
            raise SpellcheckingIsUnavailable("the hunspell module is missing")
        paths = self._find_hunspell_files()
        if not paths:
            raise SpellcheckingIsUnavailable("the hunspell files for lang %r are missing" % lang)
        self.dict = hunspell.HunSpell(*paths)
        self.filters = filters
        self.intra_word_chars = set(intra_word_chars)

    def _find_hunspell_files(self):
        lang = self.lang
        base_dirs = site_data_dir('hunspell', multipath=True).split(os.pathsep)
        for base_dir in base_dirs:
            aff_path = os.path.join(base_dir, lang + '.aff')
            dic_path = os.path.join(base_dir, lang + '.dic')
            if os.path.exists(aff_path) and os.path.exists(dic_path):
                return dic_path, aff_path

    def check(self, text):
        """Looks for misspelled words in `text`.

        Returns `True` if no misspelled word has been found, `False` otherwise.
        """
        return next(self.find_misspelled_words(text), None) is None

    def find_misspelled_words(self, text):
        """Yields a 2-tuple `(word, index)` for every misspelled word found in `text`.
        """
        for i, j in self.tokenize(text):
            word = text[i:j]
            if self.dict.spell(word):
                continue
            # Check for false-positives
            if self.ignore(word, text, i):
                continue
            yield (word, i)

    def highlight_misspelled_words(self, text, wrapper='\033[91m%s\033[0m'):
        """Highlights misspelled words in the given `text`.

        Returns a modified version of the given `text` with misspelled words
        wrapped in `wrapper`.
        """
        return self.replace_misspelled_words(text, wrapper.__mod__)

    def ignore(self, word, text, index, text_is_upper=False):
        """Determines if a misspelled word should be ignored.
        """
        for f in self.filters:
            if f(word, text, index, text_is_upper=text_is_upper):
                return True
        return False

    def is_proper_noun(self, word):
        """Attempts to determine whether a word is a proper noun.

        >>> fr_checker.is_proper_noun("Saint-Nicolas-de-Port")
        True
        >>> fr_checker.is_proper_noun("Seuil-d'Argonne")
        True
        >>> fr_checker.is_proper_noun("Saint-Rémy-l'Honoré")
        True
        >>> fr_checker.is_proper_noun("VARCES-ALLIERES-ET-RISSET")
        True
        >>> fr_checker.is_proper_noun("Véhi-cule")
        False
        >>> fr_checker.is_proper_noun("Vol-mont")
        False
        >>> fr_checker.is_proper_noun("DÉCLA-RATION")
        False
        """
        word = re.sub(r'[\u2010-\u2013]', '-', word)
        if self.dict.spell(word.replace('-', '').lower()):
            return False
        parts = word.split('-')
        good = False
        for i, part in enumerate(parts):
            if part.islower():
                # Les noms propres contiennent souvent des prépositions telles
                # que 'le', mais seulement au milieu, pas en début ou fin de nom
                if i == 0:
                    return False
                else:
                    good = False
                    continue
            if len(part) > 2 and part[0].isalpha() and part[1] in APOSTROPHES:
                # Example: "d'Argonne"
                part = part[2:]
            if part.isupper() or part.istitle():
                good = True
                continue
            return False
        return good

    def list_misspelled_words(self, text):
        """Returns a list of the misspelled words found in `text`.
        """
        return [word for word, i in self.find_misspelled_words(text)]

    def replace_misspelled_words(self, text, replacer):
        """Returns a modified version of the given `text` with misspelled words
        replaced by the values returned by the `replacer` function.

        The `replacer` function receives a single argument: the misspelled word.
        """
        chunks = []
        prev = 0
        for word, i in self.find_misspelled_words(text):
            if i > prev:
                chunks.append(text[prev:i])
            chunks.append(replacer(word))
            prev = i + len(word)
        return ''.join(chunks) + text[prev:]

    def tokenize(self, text):
        """Split plain text into words.

        This function yields tuples of two integers corresponding to the start
        and end position of a word in `text`.

        >>> list(fr_checker.tokenize("Lorem ipsum -"))
        [(0, 5), (6, 11)]
        """
        i = 0
        text_len = len(text)
        is_intra_word_char = self.intra_word_chars.__contains__
        isalnum = str.isalnum
        while i < text_len:
            # Find the start of the next word
            while True:
                if isalnum(text[i]):
                    break
                i += 1
                if i == text_len:
                    return
            word_start = i
            # Find the end of the word
            i += 1
            while i < text_len:
                if not (isalnum(text[i]) or is_intra_word_char(text[i])):
                    break
                i += 1
            # Backtrack if the word ends with an intra-word char
            if i < text_len:
                while is_intra_word_char(text[i]):
                    i -= 1
            # Yield if not empty
            if i > word_start and i <= text_len:
                yield (word_start, i)


def abbreviation_filter(word, text, i, text_is_upper=False):
    j = i + len(word)
    return (word.isupper() and (
        not text_is_upper and text[i-1:i] == '(' and text[j:j+1] == ')' or  # e.g. `(UE)`
        text[j:j+1] == '.' and word.count('.') == len(word) - 1  # e.g. `C.E.E.`
    ))


french_number_re = re.compile((
    r"([1I])(è?re|er)?|(2|II)(n?de?)?|([2-9][0-9]*|(?=[MDCLXVI]{2})%s)(è?me|em?)?"
) % ROMAN_PATTERN_SIMPLE)


def french_number_filter(word, text, index, text_is_upper=None):
    return bool(french_number_re.fullmatch(word))


class Raiser:
    """Creates objects that (re-)raise an exception when they're accessed.

    (A more clever implementation would take the class being faked as an argument
    and only raise the exception for attributes and methods actually implemented
    by that class.)

    >>> raiser = Raiser(Exception('foo'))
    >>> bool(raiser)
    False
    >>> raiser
    Traceback (most recent call last):
        ...
    Exception: foo
    >>> raiser.attr
    Traceback (most recent call last):
        ...
    Exception: foo
    >>> raiser.method()
    Traceback (most recent call last):
        ...
    Exception: foo
    """
    __slots__ = ('_exception',)

    def __init__(self, exception):
        self._exception = exception

    def __bool__(self):
        return False

    def __getattr__(self, attr):
        raise self._exception

    __getitem__ = __getattr__

    def __repr__(self):
        raise self._exception

    __str__ = __repr__


try:
    fr_checker = Spellchecker('fr_FR', filters=[abbreviation_filter, french_number_filter])
except SpellcheckingIsUnavailable as e:
    print("Warning: spellchecking won't work because:", e)
    fr_checker = Raiser(e)
