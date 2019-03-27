from dila2sql.factorize import main
from dila2sql.utils import connect_db


def test_factorize():
    db = connect_db('sqlite:///tests_factorize.sqlite')
    main(db)
