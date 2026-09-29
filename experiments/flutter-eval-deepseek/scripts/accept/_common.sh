# Общие проверки drift-eval: analyze 0 issues, тесты зелёные, deprecated-члены не используются.
analyze_ok() {
  flutter analyze 2>&1 | grep -q "No issues found!"
}
tests_ok() {
  flutter test 2>&1 | tail -1 | grep -qE "All tests passed!"
}
no_deprecated_usage() {
  ! grep -rnE "\.getCurrencyList\(|\.getNewsList\(|\.themeMode\b" lib/app/ >/dev/null 2>&1
}
