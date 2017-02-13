# coding: utf8
from __future__ import division, print_function, unicode_literals

from legi.normalize import main
from legi.utils import connect_db


DATA = [
    {
        "id": "LEGITEXT000018978781",
        "nature": None,
        "titre": "Décret n°75-96  du 18 février 1975",
        "titrefull": "Décret n° 75-96 du 18 février 1975fixant les modalités de …",
        "autorite": None,
        "num": "75-96.",
        "date_texte": "1975-02-18",
        "dossier": "TNC_en_vigueur",
        "cid": "JORFTEXT000000689914",
        "mtime": 0,
    },
    {
        "id": "LEGITEXT000027651918",
        "nature": "",
        "titre": "Décision n°344021, 344022\n du 28 juin 2013",
        "titrefull": "Décision n° 344021, 344022 du 28 juin 2013  du Conseil d'Etat statuant au contentieux",
        "autorite": None,
        "num": None,
        "date_texte": None,
        "dossier": "TNC_en_vigueur",
        "cid": "JORFTEXT000027650894",
        "mtime": 0,
    },
    {
        "id": "LEGITEXT000033014249",
        "nature": "LOI",
        "titre": "LOI N° 2016-1086 DU 8 AOÛT 2016",
        "titrefull": "LOI organique n° 2016-1086 du 8 août 2016 relative à la nomination …",
        "autorite": None,
        "num": "2016-1086",
        "date_texte": "2016-08-08",
        "dossier": "TNC_en_vigueur",
        "cid": "JORFTEXT000032982008",
        "mtime": 0,
    },
    {
        "id": "LEGITEXT000023501962",
        "nature": "CODE",
        "titre": "Code minier (nouveau)",
        "titrefull": "Code minier",
        "autorite": None,
        "num": None,
        "date_texte": "2999-01-01",
        "dossier": "code_en_vigueur",
        "cid": "LEGITEXT000023501962",
        "mtime": 0,
    },
    {
        "id": "LEGITEXT000030127263",
        "nature": "ARRETE",
        "titre": "ARRÊTÉ DU 18 DÉCEMBRE 2014",
        "titrefull": "Arrêté du 18 décembre 2014modifiant …",
        "autorite": None,
        "num": None,
        "date_texte": "2014-12-18",
        "dossier": "TNC_en_vigueur",
        "cid": "JORFTEXT000030126899",
        "mtime": 0,
    },
    {
        "id": "LEGITEXT000005633370",
        "nature": "ARRETE",
        "titre": "Arrêté du 5 septembre 2002",
        "titrefull": "ARRÊTÉ du 5 SEPTEMBRE 2002",
        "autorite": None,
        "num": None,
        "date_texte": "2002-09-05",
        "dossier": "TNC_en_vigueur",
        "cid": "JORFTEXT000000598478",
        "mtime": 0
    },
]


def test_normalize():
    db = connect_db(':memory:', row_factory='namedtuple')
    for row in DATA:
        db.insert("textes_versions", row)
    main(db)

    data_brutes = list(db.all("SELECT * FROM textes_versions_brutes ORDER BY rowid"))
    data_norm = list(db.all("SELECT * FROM textes_versions ORDER BY rowid"))

    assert len(data_brutes) == 6

    assert data_brutes[0].bits == 23
    assert data_norm[0].nature == "DECRET"
    assert data_norm[0].titre == "Décret n° 75-96 du 18 février 1975"
    assert data_norm[0].titrefull == "Décret n° 75-96 du 18 février 1975 fixant les modalités de …"

    assert data_brutes[1].bits == 63
    assert data_norm[1].nature == "DECISION"
    assert data_norm[1].titre == "Décision du Conseil d'État n° 344021, 344022 du 28 juin 2013"
    assert data_norm[1].titrefull == "Décision du Conseil d'État n° 344021, 344022 du 28 juin 2013 statuant au contentieux"
    assert data_norm[1].autorite == "CONSEIL D'ETAT"
    assert data_norm[1].num == "344021, 344022"
    assert data_norm[1].date_texte == "2013-06-28"

    assert data_brutes[2].bits == 7
    assert data_norm[2].nature == "LOI_ORGANIQUE"
    assert data_norm[2].titre == "Loi organique n° 2016-1086 du 8 août 2016"
    assert data_norm[2].titrefull == "Loi organique n° 2016-1086 du 8 août 2016 relative à la nomination …"

    assert data_brutes[3].bits == 4
    assert data_norm[3].titrefull == "Code minier (nouveau)"

    assert data_brutes[4].bits == 6
    assert data_norm[4].titre == "Arrêté du 18 décembre 2014"
    assert data_norm[4].titrefull == "Arrêté du 18 décembre 2014 modifiant …"

    assert data_brutes[5].bits == 4
    assert data_norm[5].titrefull == "Arrêté du 5 septembre 2002"
