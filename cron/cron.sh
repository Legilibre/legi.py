#!/bin/bash -eu

set -o pipefail

cd "$(dirname "$0")/.."
python -m legi.download ./tarballs
python -m legi.importer legi.sqlite ./tarballs | tee -a legi.log
