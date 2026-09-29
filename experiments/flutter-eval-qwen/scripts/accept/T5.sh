#!/usr/bin/env bash
cd "${WORKSPACE:?}" || exit 99
. "$(dirname "$0")/_common.sh"
grep -n "readThemeMode" test/unit/repository_test.dart >/dev/null || exit 1
grep -n "initAsyncData" test/unit/repository_test.dart >/dev/null || exit 1
analyze_ok || exit 1
tests_ok || exit 1
exit 0
