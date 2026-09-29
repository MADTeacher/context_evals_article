# -*- coding: utf-8 -*-
"""Слияние results/stage_*.csv в results/runs.csv.
ТОЛЬКО csv-модуль: поле status содержит переводы строк, наивный join портит файл.
Дедупликация keep-last по (задача, конфиг, idx) — перезапуски пишутся позже и
побеждают. Делает резервную копию runs.csv.bak.
Использование: py merge_runs.py <results_dir> [c0,c1,c2] [k]
Возврат 1, если после слияния остались пропуски/битые строки/флэки.
"""
import csv
import io
import os
import sys

RES = os.path.abspath(sys.argv[1])
CONFIGS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["c0", "c1", "c2"]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 5
NCOLS = 15


def read_rows(path):
    if not os.path.exists(path):
        return []
    with io.open(path, encoding="utf-8", errors="replace", newline="") as f:
        return [r for r in csv.reader(f) if r]


def main():
    tasks = ["T%d" % i for i in range(1, 9)]
    sources = [os.path.join(RES, "runs.csv")] + [
        os.path.join(RES, "stage_%s.csv" % c) for c in CONFIGS
    ]
    merged, order, dup = {}, [], []
    for path in sources:
        for r in read_rows(path):
            if len(r) < 6 or not r[0].startswith("T"):
                continue
            key = (r[0], r[1], r[2])
            if key in merged:
                dup.append(key)
            else:
                order.append(key)
            merged[key] = r
    rows = [merged[k] for k in order]

    bad = [r[:5] for r in rows if len(r) != NCOLS]
    int_bad = [r[:5] for r in rows
               if len(r) >= NCOLS and not all(x.lstrip("-").isdigit() for x in r[2:13])]
    have = {(r[0], r[1], int(r[2])) for r in rows if len(r) >= NCOLS}
    missing = [(t, c, i) for t in tasks for c in CONFIGS for i in range(1, K + 1)
               if (t, c, i) not in have]
    extra = [k for k in have if k[0] not in tasks or k[1] not in CONFIGS or not 1 <= k[2] <= K]

    out = os.path.join(RES, "runs.csv")
    if os.path.exists(out):
        with io.open(out, encoding="utf-8", errors="replace", newline="") as f:
            old = f.read()
        with io.open(out + ".bak", "w", encoding="utf-8", newline="") as f:
            f.write(old)
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for r in rows:
            w.writerow(r[:NCOLS])

    print("строк после слияния: %d (keep-last перезаписей: %d)" % (len(rows), len(dup)))
    print("битых строк: %d, нечисловых полей: %d, вне матрицы: %d"
          % (len(bad), len(int_bad), len(extra)))
    print("отсутствуют (%d): %s" % (len(missing),
          ", ".join("/".join(map(str, m)) for m in missing) or "-"))
    unresolved = ["/".join(r[:5]) for r in rows
                  if len(r) >= NCOLS and int(r[3]) != 0 and int(r[4]) != 0]
    print("rc!=0 И accept!=0: %d %s" % (len(unresolved), ", ".join(unresolved) or ""))
    envfail = ["/".join(r[:5]) for r in rows
               if len(r) >= NCOLS and int(r[3]) != 0 and int(r[4]) == 0]
    print("rc!=0 при accept=0 (цензурированные): %d %s" % (len(envfail), ", ".join(envfail) or ""))
    return 0 if not (missing or bad or int_bad or extra) else 1


if __name__ == "__main__":
    sys.exit(main())
