"""
Conversion functions for roman numbers
"""

from __future__ import division, print_function, unicode_literals


ROMAN_NUMERALS = (
    ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400), ('C', 100),
    ('XC', 90), ('L', 50), ('XL', 40), ('X', 10), ('IX', 9), ('V', 5),
    ('IV', 4), ('I', 1)
)


def decimal_to_roman(i):
    r = ''
    for numeral, value in ROMAN_NUMERALS:
        count = i // value
        r += numeral * count
        i -= value * count
    return r


def roman_to_decimal(s):
    r = 0
    i = 0
    for numeral, value in ROMAN_NUMERALS:
        l = len(numeral)
        while s[i:i+l] == numeral:
            r += value
            i += l
    if i != len(s):
        raise ValueError('"%s" is not a valid roman number' % s)
    return r
