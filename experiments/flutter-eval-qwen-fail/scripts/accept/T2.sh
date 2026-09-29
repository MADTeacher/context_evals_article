#!/usr/bin/env bash
cd "${WORKSPACE:?}" || exit 99
. "$(dirname "$0")/_common.sh"
grep -rn "fetchRates" lib/app/currency_list/ >/dev/null || exit 1
grep -rn "'USD'" lib/app/currency_list/ >/dev/null || exit 1
grep -rnE "hasMore|page \+ 1|page\+1" lib/app/currency_list/ >/dev/null || exit 1
analyze_ok || exit 1
tests_ok || exit 1
no_deprecated_usage || exit 1
exit 0
