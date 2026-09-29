# -*- coding: utf-8 -*-
"""Заполненность матрицы eval-серии: results/runs.csv + results/stage_*.csv.
Строки CSV многострочные (поле status) — читать только через csv-модуль.
Использование: py progress.py <results_dir> [T1,T2,...] [c0,c1,c2] [k]
"""
import csv
import glob
import io
import os
import sys

RES = os.path.abspath(sys.argv[1])
TASKS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["T%d" % i for i in range(1, 9)]
CONFIGS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["c0", "c1", "c2"]
K = int(sys.argv[4]) if len(sys.argv) > 4 else 5


def main():
    have = {}
    for path in [os.path.join(RES, "runs.csv")] + sorted(glob.glob(os.path.join(RES, "stage_*.csv"))):
        with io.open(path, encoding="utf-8", errors="replace", newline="") as f:
            for r in csv.reader(f):
                if len(r) >= 6 and r[0].startswith("T") and r[1] in CONFIGS:
                    have[(r[0], r[1], int(r[2]))] = (int(r[3]), int(r[4]))
    total = len(have)
    print("прогресс: %d/%d" % (total, len(TASKS) * len(CONFIGS) * K))
    for c in CONFIGS:
        line = "  %s: " % c
        for t in TASKS:
            n = sum(1 for (tt, cc, i) in have if tt == t and cc == c)
            ok = sum(1 for (tt, cc, i), (rc, acc) in have.items() if tt == t and cc == c and rc == 0 and acc == 0)
            line += "%s %d/%d | " % (t, ok, n)
        print(line)
    flaky = ["%s__%s__%d rc=%d acc=%d" % (t, c, i, rc, acc)
             for (t, c, i), (rc, acc) in sorted(have.items()) if rc != 0 and acc != 0]
    print("флэки (rc!=0 и accept!=0): %s" % (", ".join(flaky) if flaky else "нет"))
    envfail = ["%s__%s__%d rc=%d acc=%d" % (t, c, i, rc, acc)
               for (t, c, i), (rc, acc) in sorted(have.items()) if rc != 0 and acc == 0]
    print("обрывы сессий (rc!=0 при accept=0 — цензурированные, тоже перезапускать): %s"
          % (", ".join(envfail) if envfail else "нет"))


if __name__ == "__main__":
    main()
