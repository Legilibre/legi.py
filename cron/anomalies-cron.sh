#!/bin/bash -eu

cd "$(dirname "$0")/.."
mkdir -p tarballs
( cd tarballs && wget -c -N --no-remove-listing -nH 'ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/*legi_*' )
echo "=> Starting tar2sqlite..."
python -m legi.tar2sqlite legi.raw.sqlite tarballs --anomalies --anomalies-dir=anomalies | tee -a legi.raw.log
echo "=> Uploading anomaly logs..."
rsync anomalies/ $1:~/anomalies/logs -rtv --chmod=F644
echo "=> Generating index.html..."
python cron/anomalies-stats.py anomalies | ssh $1 'umask 022 && cat >~/anomalies/index.html'
