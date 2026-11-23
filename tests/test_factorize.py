from legi.db import connect_db
from legi.factorize import run


def test_factorize():
    db = connect_db(':memory:')
    run(db)
