#!/usr/bin/env bash
# Батч drift-eval: до ~25 минут работы за вызов, сам пропускает сделанное.
# Использование: batch_drift.sh <c0|c1|c2>
set -u
C="${1:?c0|c1|c2}"
ROOT="/c/Users/MADTeacher/Documents/GitHub/context_article_repo/experiments/flutter-eval-qwen"
START=$(date +%s)

todo=$(py - "$C" "$ROOT" <<'PY'
import csv, io, os, sys
c, root = sys.argv[1], sys.argv[2]
have = set()
for f in ["runs.csv"] + [os.path.basename(p) for p in __import__("glob").glob(os.path.join(root, "results", "stage_*.csv"))]:
    try:
        raw = io.open(os.path.join(root, "results", f), encoding="utf-8", errors="replace").read()
        for r in csv.reader(io.StringIO(raw)):
            if len(r) >= 6 and r[0].startswith("T") and r[1] == c and r[2].isdigit() and r[3].isdigit() and r[4].isdigit():
                have.add((r[0], int(r[2])))
    except Exception:
        pass
todo = []
for t in ["T1","T2","T3","T4","T5","T6","T7","T8"]:
    for i in range(1, 6):
        if (t, i) not in have:
            todo.append(f"{t},{i}")
print(";".join(todo))
PY
)
FAILS=0
for pair in ${todo//;/ }; do
  [ -z "$pair" ] && continue
  T="${pair%,*}"; I="${pair#*,}"
  ELAPSED=$(( $(date +%s) - START ))
  if [ $ELAPSED -gt 1500 ]; then
    echo "batch $C: time budget reached (остались прогоны)"
    exit 0
  fi
  if bash "$ROOT/scripts/run_one.sh" "$T" "$C" "$I"; then
    FAILS=0
  else
    FAILS=$((FAILS+1))
    if [ "$FAILS" -ge 3 ]; then
      echo "batch $C: 3 прогона подряд rc!=0 (сеть/API?) — стоп батча до оздоровления"
      exit 3
    fi
  fi
done
echo "batch $C: всё сделано"
