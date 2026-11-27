#!/bin/sh
# Statik testler: Penpot export/import (mock sunucu). Docker gerekmez.
# Kullanım: tests/run_static.sh
set -u
cd "$(dirname "$0")/.." || exit 2
rc=0
export PYTHONDONTWRITEBYTECODE=1
for t in tests/test_penpot_transfer.py; do
  echo "== $t"
  python3 -I "$t" || rc=1
done
[ $rc -eq 0 ] && echo "ALL STATIC TESTS PASSED" || echo "SOME STATIC TESTS FAILED"
exit $rc
