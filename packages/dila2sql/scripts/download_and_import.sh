#!/bin/sh

python -m dila2sql.download --base KALI
python -m dila2sql.importer --base KALI --raw postgresql://legipy:dilamite@10.200.107.153/kali
