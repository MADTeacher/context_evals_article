#!/usr/bin/env bash
# Один прогон drift-eval: свежая копия fixture(v2) -> инжект конфигурации ->
# madharness run -> приёмка -> CSV. Использование: run_one.sh <T1..T8> <c0|c1|c2> <idx>
set -u
T="$1"; C="$2"; I="$3"
ROOT="/c/Users/MADTeacher/Documents/GitHub/context_article_repo/experiments/flutter-eval-qwen"
KEYFILE="/c/Users/MADTeacher/Documents/GitHub/context_article_repo/experiments/flutter-eval-qwen/contexts/local-key.json"
WT="$ROOT/workspaces/run/${T}__${C}__${I}"
WINWT=$(cygpath -w "$WT")
WINROOT=$(cygpath -w "$ROOT")

rm -rf "$WT"
mkdir -p "$WT"
(cp -r "$ROOT/fixture/." "$WT/") && rm -rf "$WT/.git" "$WT/build" "$WT/.dart_tool"

mkdir -p "$WT/.madharness-mini" "$WT/scripts/hooks"
py - "$WINWT" "$KEYFILE" "$WINROOT" <<'PYEOF'
import json, io, os, sys
wt, keyfile, root = sys.argv[1], sys.argv[2], sys.argv[3]
tpl = io.open(os.path.join(root, "contexts", "config.template.json"), encoding="utf-8").read()
key = json.load(io.open(keyfile, encoding="utf-8"))["api_key"]
cfg = tpl.replace("__API_KEY__", key)
io.open(os.path.join(wt, ".madharness-mini", "config.json"), "w", encoding="utf-8", newline="\n").write(cfg)
PYEOF

case "$C" in
  c0) ;;
  c1)
    cp "$ROOT/contexts/c1/AGENTS.md" "$WT/AGENTS.md"
    mkdir -p "$WT/.agents/skills"
    cp -r "$ROOT/skills-src/"*/ "$WT/.agents/skills/"
    ;;
  c2)
    cp "$ROOT/contexts/c2/AGENTS.md" "$WT/AGENTS.md"
    cp "$ROOT/contexts/c2/app/AGENTS.md" "$WT/lib/app/AGENTS.md"
    cp "$ROOT/contexts/c2/data/AGENTS.md" "$WT/lib/data/AGENTS.md"
    cp "$ROOT/contexts/c2/domain/AGENTS.md" "$WT/lib/domain/AGENTS.md"
    mkdir -p "$WT/.agents/skills"
    cp -r "$ROOT/contexts/c2/skills/migration-v2" "$WT/.agents/skills/"
    cp -r "$ROOT/skills-src/flutter-testing" "$WT/.agents/skills/"
    cp "$ROOT/contexts/c2/hooks/hooks.json" "$WT/.madharness-mini/hooks.json"
    cp "$ROOT/contexts/c2/scripts/hooks/guard_v2.py" "$WT/scripts/hooks/guard_v2.py"
    ;;
  *) echo "unknown config: $C"; exit 99 ;;
esac

START=$(date +%s)
cd "$WT"
timeout 5400 madharness-mini run "$(cat "$ROOT/protocol/scenarios/$T.txt")" \
  > "$ROOT/results/logs/${T}__${C}__${I}.out" 2>&1
RC=$?
DUR=$(( $(date +%s) - START ))
cd "$ROOT"

TRACE=$(ls -t "$WT/.madharness-mini/traces/"*.jsonl 2>/dev/null | head -1)
TF="$ROOT/results/traces/${T}__${C}__${I}.jsonl"
if [ -n "${TRACE:-}" ]; then cp "$TRACE" "$TF"; else TF="none"; fi

WORKSPACE="$WINWT" bash "$ROOT/scripts/accept/$T.sh" >/dev/null 2>&1
ACC=$?

CSV="$ROOT/results/runs.csv"
[ -n "${STREAM:-}" ] && CSV="$ROOT/results/stage_$STREAM.csv"
py scripts/trace_row.py "$T" "$C" "$I" "$RC" "$ACC" 0 0 "$DUR" "$TF" >> "$CSV"
echo "done: $T $C $I rc=$RC accept=$ACC dur=${DUR}s"
[ "$RC" -ne 0 ] && exit 1
exit 0
