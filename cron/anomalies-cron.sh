#!/bin/bash -eu

set -o pipefail

cd "$(dirname "$0")/.."
wget -c -N --no-remove-listing -nH -P ./tarballs 'ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/*legi_*'
echo "=> Starting tar2sqlite..."
python -m legi.tar2sqlite legi.raw.sqlite tarballs --anomalies --anomalies-dir=anomalies | tee -a legi.raw.log
echo "=> Uploading anomaly logs..."
rsync anomalies/ $1:~/anomalies/logs -rtv --chmod=F644
echo "=> Generating index.html..."
f=tmp_anomalies-index.html
python cron/anomalies-stats.py anomalies >$f
[ -s $f ] && rsync $f $1:~/anomalies/index.html -tv --chmod=F644
rm $f
