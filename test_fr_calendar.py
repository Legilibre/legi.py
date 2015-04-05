from __future__ import division, print_function, unicode_literals

from datetime import timedelta

from fr_calendar import (
    MOIS_REPU, REPUBLICAN_START_DATE, SANSCULOTTIDES,
    gregorian_to_republican, republican_to_gregorian,
)


def test_continuity():
    one_day = timedelta(days=1)
    greg = REPUBLICAN_START_DATE
    for year in range(1, 500):
        for month in MOIS_REPU:
            for day in range(1, 31):
                assert republican_to_gregorian(year, month, day) == greg
                assert gregorian_to_republican(greg.year, greg.month, greg.day) == (year, month, day)
                greg += one_day
        for day in SANSCULOTTIDES[:5 + (year % 4 == 3)]:
            assert republican_to_gregorian(year, None, day) == greg
            assert gregorian_to_republican(greg.year, greg.month, greg.day) == (year, None, day)
            greg += one_day
