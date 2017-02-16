#!/bin/bash -eu

set -o pipefail

cd "$(dirname "$0")/.."
python -m legi.download ./tarballs
python -m legi.tar2sqlite legi.sqlite ./tarballs | tee -a legi.log
