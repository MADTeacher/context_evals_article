# -*- coding: utf-8 -*-
"""Сравнение C2 до (итерация 1) и после (итерация 2) эволюции жизненного цикла.
Пишет results/analysis/iter2-comparison.md."""
import csv
import io
import json
import math
import os
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
TASKS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
Z = 1.959964


def wilson(k, n):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def pct(x):
    return ("%.2f" % x).replace(".", ",")


def fmt(k, n):
    if n == 0:
        return "—"
    p, lo, hi = wilson(k, n)
    return "%d/%d; %s [%s; %s]" % (k, n, pct(p), pct(lo), pct(hi))


def load_rows(path, cfg):
    rows = []
    with io.open(path, encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 15 and r[0].startswith("T") and r[1] == cfg:
                rows.append({"T": r[0], "I": int(r[2]), "rc": int(r[3]), "acc": int(r[4]),
                             "dur": int(r[7]), "turns": int(r[8]),
                             "tin": int(r[9]), "tout": int(r[10]), "blocked": int(r[12]),
                             "skills": r[13]})
    return rows


def trace_turns(path):
    turns = 0
    if not os.path.exists(path):
        return 0
    for line in io.open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("event") == "model_usage":
            turns = max(turns, int(e.get("turn") or 0))
    return turns


def load_trace(path):
    skills, blocked, turns, tin, tout = set(), 0, 0, 0, 0
    if not os.path.exists(path):
        return None
    for line in io.open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        ev = e.get("event", "")
        if ev == "skill_activated":
            skills.add(e.get("skill") or e.get("name") or "?")
        elif ev == "hook_blocked":
            blocked += 1
        elif ev == "model_usage":
            turns = max(turns, int(e.get("turn") or 0))
            tin += int(e.get("prompt_tokens") or 0)
            tout += int(e.get("completion_tokens") or 0)
    return {"skills": skills, "blocked": blocked, "turns": turns, "tin": tin, "tout": tout}


def main():
    before = load_rows(os.path.join(RES, "iter1", "runs.csv"), "c2")
    after = load_rows(os.path.join(RES, "stage_c2.csv"), "c2")

    def ok(r):
        return r["rc"] == 0 and r["acc"] == 0

    L = []
    w = L.append
    w("# C2: итерация 1 (ЖЦ v1) → итерация 2 (ЖЦ v2, эволюция по триажу)")
    w("")
    w("| Задача | До (v1) | После (v2) | Δp̂ |")
    w("| --- | --- | --- | --- |")
    kb = ka = nb = na = 0
    for t in TASKS:
        b = [r for r in before if r["T"] == t]
        a = [r for r in after if r["T"] == t]
        kb += sum(map(ok, b)); nb += len(b)
        ka += sum(map(ok, a)); na += len(a)
        pb = sum(map(ok, b)) / len(b) if b else 0
        pa = sum(map(ok, a)) / len(a) if a else 0
        w("| %s | %s | %s | %+s |" % (t, fmt(sum(map(ok, b)), len(b)),
                                       fmt(sum(map(ok, a)), len(a)),
                                       pct(pa - pb)))
    w("| **Итого C2** | **%s** | **%s** | **%+s** |" % (
        fmt(kb, nb), fmt(ka, na), pct(ka / na - kb / nb)))
    w("")

    # Ресурсы (ходы — из трасс: в CSV колонка ходов всегда 0)
    for label, rows, tr_dir in (("До (v1)", before, os.path.join(RES, "iter1", "traces")),
                                ("После (v2)", after, os.path.join(RES, "traces"))):
        tv = [trace_turns(os.path.join(tr_dir, "%s__c2__%d.jsonl" % (r["T"], r["I"])))
              for r in rows]
        w("- %s: средние входные токены %.0f тыс., ходы %.1f, длительность %.0f с"
          % (label,
             statistics.mean(r["tin"] for r in rows) / 1000,
             statistics.mean(tv),
             statistics.mean(r["dur"] for r in rows)))
    w("")

    # Навыки/хуки по трассам итерации 2
    act = sum(1 for r in after if r["skills"])
    blocked_runs = [r for r in after if r["blocked"] > 0]
    w("- Итерация 2: активация migration-v2 в %d/%d прогонов; блокировок V-хука: %d (в %d прогонах)."
      % (act, len(after), sum(r["blocked"] for r in after), len(blocked_runs)))
    w("")

    # Остаточные неудачи
    fails = [(r["T"], r["rc"], r["acc"]) for r in after if not ok(r)]
    if fails:
        w("- Остаточные неудачи итерации 2 (класс (2), ограничение модели): %s."
          % "; ".join("%s (rc=%d, accept=%d)" % (t, rc, acc) for t, rc, acc in fails))
        w("  T2/c2/3 — пагинация не доведена до конвенций v2; T6/c2/3 — неиспользуемый импорт (info-линт).")
    else:
        w("- Остаточных неудач итерации 2 нет.")
    w("")

    out = os.path.join(RES, "analysis", "iter2-comparison.md")
    io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print("написан", out)
    print("C2: до %d/%d → после %d/%d" % (kb, nb, ka, na))


if __name__ == "__main__":
    main()
