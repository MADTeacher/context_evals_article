#!/usr/bin/env bash
cd "${WORKSPACE:?}" || exit 99
. "$(dirname "$0")/_common.sh"
N=$(grep -c "loadNewsFeed" lib/app/news_list/news_list_page.dart)
[ "$N" -ge 2 ] || exit 1
grep -rn "forceRefresh: true" lib/app/news_list/ >/dev/null || exit 1
grep -rn "forceRefresh: false\|NewsFeedFilter.all" lib/app/news_list/ >/dev/null || exit 1
analyze_ok || exit 1
tests_ok || exit 1
no_deprecated_usage || exit 1
exit 0
