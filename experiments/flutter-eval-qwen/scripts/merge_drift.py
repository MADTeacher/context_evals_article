# -*- coding: utf-8 -*-
"""Слияние stage_c*.csv в results/runs.csv (только csv-модуль: поле status
содержит переводы строк). Дедупликация keep-last по (задача, конфиг, idx).
Использование: py scripts/merge_drift.py
"""
import csv
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
TASKS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
CONFIGS = ["c0", "c1", "c2"]
NCOLS = 15


def read_rows(path):
    if not os.path.exists(path):
        return []
    with io.open(path, encoding="utf-8", errors="replace", newline="") as f:
        return [r for r in csv.reader(f) if r]


def main():
    sources = [os.path.join(RES, "runs.csv")] + [
        os.path.join(RES, "stage_%s.csv" % c) for c in CONFIGS
    ]
    merged = {}
    order = []
    dup = []
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

    bad = [r for r in rows if len(r) != NCOLS]
    int_bad = [
        r[:5] for r in rows
        if len(r) >= NCOLS and not all(x.lstrip("-").isdigit() for x in r[2:13])
    ]
    have = {(r[0], r[1], int(r[2])) for r in rows if len(r) >= NCOLS}
    missing = [
        (t, c, i)
        for t in TASKS
        for c in CONFIGS
        for i in range(1, 6)
        if (t, c, i) not in have
    ]
    extra = [k for k in have if k[0] not in TASKS or k[1] not in CONFIGS or not 1 <= k[2] <= 5]

    out = os.path.join(RES, "runs.csv")
    bak = out + ".bak"
    if os.path.exists(out):
        with io.open(out, encoding="utf-8", errors="replace", newline="") as f:
            old = f.read()
        with io.open(bak, "w", encoding="utf-8", newline="") as f:
            f.write(old)
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for r in rows:
            w.writerow(r[:NCOLS])

    print("источники: %s" % ", ".join(os.path.basename(p) for p in sources))
    print("строк после слияния: %d (дублей перезаписано keep-last: %d)" % (len(rows), len(dup)))
    if dup:
        print("  keep-last по:", ", ".join("/".join(k) for k in dup))
    print("битых строк (len!=%d): %d" % (NCOLS, len(bad)))
    print("нечисловых полей 3-12: %d" % len(int_bad))
    print("отсутствуют (%d): %s" % (len(missing), ", ".join("/".join(map(str, k)) for k in missing) or "-"))
    print("вне матрицы: %s" % (", ".join("/".join(map(str, k)) for k in extra) or "-"))
    unresolved = [
        "/".join(r[:5]) for r in rows
        if len(r) >= NCOLS and (int(r[3]) != 0 and int(r[4]) != 0)
    ]
    print("строк с rc!=0 И accept!=0 (кандидаты в перезапуск): %d %s"
          % (len(unresolved), ", ".join(unresolved) or ""))
    return 0 if not missing and not bad and not int_bad and not extra else 1


if __name__ == "__main__":
    sys.exit(main())
