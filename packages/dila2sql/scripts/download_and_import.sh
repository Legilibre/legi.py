#!/bin/sh

python -m dila2sql.download --base KALI
echo LOOOOL
python -m dila2sql.importer --base KALI --raw postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/kali
echo FINISHED
