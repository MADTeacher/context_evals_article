#!/usr/bin/env bash
# Поток серии drift-eval: health-гейт + цикл батчей до "всё сделано".
# Журнал этапов: results/logs/runner_<c>.log (диагностика зависаний).
# Использование: bash scripts/stream_runner.sh <c0|c1|c2>
set -u
C="${1:?c0|c1|c2}"
ROOT="/c/Users/MADTeacher/Documents/GitHub/context_article_repo/experiments/flutter-eval-qwen"
LOG="$ROOT/results/logs/batch_$C.log"
RLOG="$ROOT/results/logs/runner_$C.log"
cd "$ROOT" || exit 9
export no_proxy="127.0.0.1,169.254.83.107,localhost" NO_PROXY="127.0.0.1,169.254.83.107,localhost"
note() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> "$RLOG"; }
while :; do
  note "ожидание здоровья API"
  until py scripts/api_health.py >/dev/null 2>&1; do sleep 300; done
  note "API здоров, запуск batch_drift"
  STREAM="$C" bash scripts/batch_drift.sh "$C" >> "$LOG" 2>&1
  RC=$?
  note "batch_drift завершился, rc=$RC"
  if tail -n 3 "$LOG" | grep -q "всё сделано"; then
    note "поток завершён"
    break
  fi
  note "батч не доложил 'всё сделано' — цикл продолжается"
done
note "ФИНИШ"
echo "STREAM-${C}-FINISHED"
