import urllib.request
import shutil
import xlrd
from argparse import ArgumentParser
from dila2sql.utils import connect_db
from dila2sql.models import db_proxy, Conteneur
import os.path
import csv

XLS_URL = "https://travail-emploi.gouv.fr/IMG/xls/idccavril19.xls"
FILE_PATH = './travail_gouv_active_idccs.xls'
MISSING_FILE_PATH = './missing_idccs.%s.csv'

# ALTER TABLE conteneurs ADD COLUMN active BOOLEAN;


def download_file(use_cache=True):
    if os.path.isfile(FILE_PATH) and use_cache:
        return
    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(XLS_URL) as response, open(FILE_PATH, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def get_active_idccs(xls_sheet):
    raw_idccs = [cell.value for cell in xls_sheet.col(0)][4:]
    # some look like 3221.0
    # in the KALI db, nums are not padded, so this should remove padding
    return [str(int(idcc)) for idcc in raw_idccs]


def identify_missing(xls_sheet, num_lower_bound=0, num_upper_bound=9999, group='all'):
    idccs_in_xls = [
        num for num in active_idccs
        if int(num) >= num_lower_bound and int(num) < num_upper_bound
    ]
    print("there are %s active IDCCs from the %s in the XLS" % (len(idccs_in_xls), group))
    conteneurs = Conteneur.select(Conteneur.num).where(Conteneur.num.in_(idccs_in_xls))
    idccs_in_kali = [c.num for c in conteneurs]
    print("found %s IDCCs amongst these from the %s in the KALI DB" % (len(idccs_in_kali), group))
    missing_ones = set(idccs_in_xls) - set(idccs_in_kali)
    missing_pairs = []
    for idx, row in enumerate(xls_sheet.get_rows()):
        if idx < 4:
            continue
        row_idcc = str(int(row[0].value))
        if row_idcc in missing_ones:
            missing_pairs.append([row_idcc, row[1].value])
    file_path = MISSING_FILE_PATH % group
    with open(file_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerows([["idcc", "name"]])
        writer.writerows(missing_pairs)
    if len(missing_ones) != len(missing_pairs):
        raise "error when looking for missing idccs"
    print("wrote %s missing %s IDCCs to %s" % (len(missing_pairs), group, file_path))


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('db')
    p.add_argument('--identify-missing', action='store_true')
    p.add_argument('--force-download', action='store_true')
    args = p.parse_args()

    print("starting download of %s..." % XLS_URL)
    download_file(not args.force_download)
    print("file downloaded!")

    xls_sheet = xlrd.open_workbook(FILE_PATH).sheet_by_index(0)

    active_idccs = get_active_idccs(xls_sheet)
    print("got %s ACTIVE IDCCS in file" % len(active_idccs))

    db = connect_db(args.db)
    db_proxy.initialize(db)

    if args.identify_missing:
        identify_missing(xls_sheet, 0, 3999, 'DGT')
        identify_missing(xls_sheet, 5000, 5999, 'DARES')
        identify_missing(xls_sheet, 7000, 9999, 'AGRICULTURE')

    Conteneur.update(active=False).execute()
    count = Conteneur.update(active=True) \
        .where(Conteneur.num.in_(active_idccs)) \
        .execute()
    print("marked %s conteneurs as active!" % count)
