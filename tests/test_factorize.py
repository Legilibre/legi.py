from legi.db import connect_db
from legi.factorize import main


def test_factorize():
    db = connect_db(':memory:')
    main(db)
