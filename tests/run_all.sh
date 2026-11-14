#!/usr/bin/env bash
# Runs every available language test; Java and Dart are skipped (no test harness / toolchain yet).
set -u
cd "$(dirname "$0")"
rc=0
run() { echo "== $1"; shift; "$@" || rc=1; }
run python python3 -m unittest -v test_python
run javascript node --test test_javascript.js
run c bash -c 'gcc -Wall -o /tmp/vietqr_ctest test_c.c ../C/vietqr.c && /tmp/vietqr_ctest'
run go bash -c 'cd ../go && go test ./...'
exit $rc
