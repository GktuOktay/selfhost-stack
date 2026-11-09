#!/bin/sh
# Runs every static test of spec 0002 Faz 1 (docker needed for the pinned BookStack image; nothing is pulled).
# Usage: tests/run_static.sh
set -u
cd "$(dirname "$0")/.." || exit 2
rc=0
export PYTHONDONTWRITEBYTECODE=1
for t in tests/test_blade_scan.py tests/test_cb7_static.py tests/test_cb8_upstream.py \
         tests/test_upgrade_diff_check.py tests/test_render.py; do
  echo "== $t"
  python3 -I "$t" || rc=1
done
echo "== CB-8 on the real theme"
python3 -I tests/cb8_upstream_check.py || rc=1
echo "== CB-7 (d)(e)(f) on the real theme"
python3 -I tests/cb7_static_check.py || rc=1
[ $rc -eq 0 ] && echo "ALL STATIC TESTS PASSED" || echo "SOME STATIC TESTS FAILED"
exit $rc
