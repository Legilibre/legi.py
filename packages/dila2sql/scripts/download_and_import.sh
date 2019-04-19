#!/bin/sh
dkjxzbvbkcbhxkz sdajkvjk vdfsv qeba

python -m dila2sql.download --base KALI
python -m dila2sql.importer --base KALI --raw postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/kali
