# encoding: utf8

"""
A module to handle dates from the French Republican Calendar
"""

from __future__ import division, print_function, unicode_literals

from datetime import date, timedelta

from roman import roman_to_decimal
from utils import strip_down


MOIS_REPU = 'vendémiaire brumaire frimaire nivôse pluviôse ventôse germinal floréal prairial messidor thermidor fructidor'.split()
MOIS_REPU_MAP = {strip_down(m): i for i, m in enumerate(MOIS_REPU, 1)}
REPUBLICAN_START_DATE = date(1792, 9, 22)
SANSCULOTTIDES = (
    "Jour de la vertu", "Jour du génie", "Jour du travail",
    "Jour de l'opinion", "Jour des récompenses", "Jour de la révolution"
)
SANSCULOTTIDES_MAP = {strip_down(d): i for i, d in enumerate(SANSCULOTTIDES, 1)}


def gregorian_to_republican(year, month, day):
    days = (date(year, month, day) - REPUBLICAN_START_DATE).days
    sextiles = (days + 366) // 1461
    sextile = (days + 366) % 1461 == 0
    days -= sextiles
    year = days // 365 + 1
    days -= (year - 1) * 365
    month = days // 30 + 1
    day = days % 30 + 1
    if month == 13:
        day = SANSCULOTTIDES[day - 1 + sextile]
        month = None
    else:
        month = MOIS_REPU[month - 1]
    return year, month, day


def republican_to_gregorian(year, month, day):
    if not isinstance(year, int):
        year = roman_to_decimal(year)
    month = MOIS_REPU_MAP[strip_down(month)] if month else 13
    if month == 13:
        day = SANSCULOTTIDES_MAP[strip_down(day)]
    d = (year - 1) * 365 + (month - 1) * 30 + day - 1 + year // 4
    return REPUBLICAN_START_DATE + timedelta(days=d)
