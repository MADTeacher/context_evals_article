# -*- coding: utf-8 -*-
"""Прогресс серии drift-eval: заполненность матрицы 8×3×5 по stage/runs файлам."""
import csv
import glob
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def main():
    have = {}
    for path in [os.path.join(RES, "runs.csv")] + sorted(glob.glob(os.path.join(RES, "stage_*.csv"))):
        with io.open(path, encoding="utf-8", errors="replace", newline="") as f:
            for r in csv.reader(f):
                if len(r) >= 6 and r[0].startswith("T") and r[1] in ("c0", "c1", "c2"):
                    have[(r[0], r[1], int(r[2]))] = (int(r[3]), int(r[4]))
    total = len(have)
    print("прогресс: %d/120" % total)
    for c in ("c0", "c1", "c2"):
        line = "  %s: " % c
        for t in ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"):
            n = sum(1 for (tt, cc, i) in have if tt == t and cc == c)
            ok = sum(1 for (tt, cc, i), (rc, acc) in have.items() if tt == t and cc == c and rc == 0 and acc == 0)
            line += "%s %d/%d | " % (t, ok, n)
        print(line)
    flaky = ["%s__%s__%d rc=%d acc=%d" % (t, c, i, rc, acc)
             for (t, c, i), (rc, acc) in sorted(have.items()) if rc != 0 and acc != 0]
    print("флэки (rc!=0 и accept!=0): %s" % (", ".join(flaky) if flaky else "нет"))


if __name__ == "__main__":
    main()
