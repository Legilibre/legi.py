#!/bin/sh
echo "Error blabla!" 1>&2
exit 1
python -m dila2sql.download --base KALI
python -m dila2sql.importer --base KALI --raw postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/kali
