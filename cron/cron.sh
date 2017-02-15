#!/bin/bash -eu

set -o pipefail

cd "$(dirname "$0")/.."
wget -c -N --no-remove-listing -nH -P ./tarballs 'ftp://legi:open1234@ftp2.journal-officiel.gouv.fr/*legi_*'
(
    echo "=> Running tar2sqlite..."
    python -m legi.tar2sqlite legi.sqlite tarballs
    echo "=> Running normalize..."
    python -m legi.normalize legi.sqlite
    echo "=> Running factorize..."
    python -m legi.factorize legi.sqlite
) | tee -a legi.log
