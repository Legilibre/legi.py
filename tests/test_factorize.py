from __future__ import division, print_function, unicode_literals

from legi.factorize import main
from legi.utils import connect_db


def test_factorize():
    db = connect_db(':memory:')
    main(db)
