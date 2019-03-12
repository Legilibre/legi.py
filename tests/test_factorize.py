from legi.factorize import main
from legi.utils import connect_db


def test_factorize():
    db = connect_db('sqlite:///tests_factorize.sqlite')
    main(db)
