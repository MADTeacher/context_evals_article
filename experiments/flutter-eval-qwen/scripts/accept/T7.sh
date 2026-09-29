#!/usr/bin/env bash
cd "${WORKSPACE:?}" || exit 99
. "$(dirname "$0")/_common.sh"
grep -rn "fetchRates" lib/app/ >/dev/null || exit 1
grep -rn "loadNewsFeed" lib/app/ >/dev/null || exit 1
N=$(ls changelog/*.rst 2>/dev/null | wc -l)
[ "$N" -ge 3 ] || exit 1
analyze_ok || exit 1
tests_ok || exit 1
no_deprecated_usage || exit 1
exit 0
