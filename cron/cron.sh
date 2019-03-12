#!/bin/bash -eu

set -o pipefail

cd "$(dirname "$0")/.."
python -m dila2sql.download ./tarballs
python -m dila2sql.importer legi.sqlite ./tarballs | tee -a legi.log
