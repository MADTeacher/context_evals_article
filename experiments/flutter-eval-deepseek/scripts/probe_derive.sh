#!/usr/bin/env bash
# Зонд выводимости (методика v1.1, §7а): N агентов C0 на задаче T1 (конвенция
# base:'USD' невыводима из v3-фикстуры). БЕЗ записи в runs/stage CSV.
# Гейт дизайна серии: если >= 2 из N сдают приёмку — конвенция выводима из
# репозитория, полигон течёт: СТОП и разбор, серию не запускать.
# Использование: bash scripts/probe_derive.sh [N] [T]
set -u
N="${1:-3}"
T="${2:-T1}"
ROOT="/c/Users/MADTeacher/Documents/GitHub/context_article_repo/experiments/flutter-eval-deepseek"
KEYFILE="$ROOT/contexts/local-key.json"
mkdir -p "$ROOT/results/probe/logs" "$ROOT/results/probe/traces" "$ROOT/workspaces/probe"
PASS=0
for i in $(seq 1 "$N"); do
  WT="$ROOT/workspaces/probe/${T}__c0__P${i}"
  WINWT=$(cygpath -w "$WT")
  WINROOT=$(cygpath -w "$ROOT")
  rm -rf "$WT"; mkdir -p "$WT"
  (cp -r "$ROOT/fixture/." "$WT/") && rm -rf "$WT/.git" "$WT/build" "$WT/.dart_tool"
  mkdir -p "$WT/.madharness-mini"
  py - "$WINWT" "$KEYFILE" "$WINROOT" <<'PYEOF'
import json, io, os, sys
wt, keyfile, root = sys.argv[1], sys.argv[2], sys.argv[3]
tpl = io.open(os.path.join(root, "contexts", "config.template.json"), encoding="utf-8").read()
key = json.load(io.open(keyfile, encoding="utf-8"))["api_key"]
io.open(os.path.join(wt, ".madharness-mini", "config.json"), "w", encoding="utf-8", newline="\n").write(tpl.replace("__API_KEY__", key))
PYEOF
  cd "$WT"
  timeout 1800 madharness-mini run "$(cat "$ROOT/protocol/scenarios/$T.txt")" \
    > "$ROOT/results/probe/logs/${T}__c0__P${i}.out" 2>&1
  RC=$?
  cd "$ROOT"
  TRACE=$(ls -t "$WT/.madharness-mini/traces/"*.jsonl 2>/dev/null | head -1)
  [ -n "${TRACE:-}" ] && cp "$TRACE" "$ROOT/results/probe/traces/${T}__c0__P${i}.jsonl"
  WORKSPACE="$WINWT" bash "$ROOT/scripts/accept/$T.sh" >/dev/null 2>&1
  ACC=$?
  echo "probe: $T c0 P$i rc=$RC accept=$ACC"
  [ "$RC" -eq 0 ] && [ "$ACC" -eq 0 ] && PASS=$((PASS+1))
done
echo "probe: сдали $PASS/$N (гейт: >=2 PASS = полигон течёт, серию НЕ запускать)"
[ "$PASS" -lt 2 ]
