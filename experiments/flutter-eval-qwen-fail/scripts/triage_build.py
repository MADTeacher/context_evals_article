# -*- coding: utf-8 -*-
"""Сборка results/analysis/triage.csv из triage_scan2.txt (классы 1/2/3)."""
import csv
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = os.path.join(ROOT, "results", "analysis", "triage_scan2.txt")
OUT = os.path.join(ROOT, "results", "analysis", "triage.csv")


def classify(t, c, check, first):
    """Возвращает (class, subclass, note)."""
    note = check
    sub = ""
    # 1) l10n: правка ARB без регенерации
    if "AppLocalizations" in first or re.search(r"getter '(showMore|loadMore|refresh|refreshAll|dashboard)'", first) or "'loc'" in first:
        if c == "c2":
            return "1", "", "l10n: ключ использован без flutter.bat gen-l10n — workflow не был в контексте (добавлен в v2)"
        return "2", "", "l10n: правка ARB без регенерации — undefined getter"
    # 2) info-линт: неиспользуемые импорты/поля/скобки
    if "unnecessary" in first or "unused" in first or "isn't used" in first or "isn't referenced" in first:
        return "2", "", "info-линт (analyze требует нуля замечаний): " + first[:80]
    # 3) dart:async
    if "Completer" in first or "StreamSubscription" in first:
        return "2", "", "нет импорта dart:async — " + first[:80]
    # 4) структурные требования задачи
    if check.startswith("grep") or check.startswith("changelog"):
        known = {
            "grep пагинация": "пагинация не доведена до конвенций v2 (hasMore/page+1)",
            "grep loadNewsFeed>=2": "loadNewsFeed должен вызываться в обеих ветках обновления (кэш и сеть)",
            "grep forceRefresh:false|all": "не реализована ветка forceRefresh: false / NewsFeedFilter.all",
            "grep Future.wait": "параллельная загрузка через Future.wait не реализована",
            "changelog>=3": "менее трёх changelog-фрагментов на многочастное изменение",
        }
        note = known.get(check, check)
        if check == "grep loadNewsFeed>=2" and c == "c2":
            return "1", "", "конвенция «вызов в обеих ветках» не была сообщена контекстом (прецедент серии deepseek); в v2 не добавлялась"
        if check == "changelog>=3" and c == "c2":
            return "1", "", "правило «фрагмент на каждое изменение» в контексте сформулировано без нормы для многочастных задач"
        return "2", "", note
    # 5) падение тестов
    if check.startswith("tests:"):
        return "2", "", "падение тестов (собственных/существующих) при приёмке"
    # 6) прочие ошибки компиляции/кода
    return "2", "", "дефект кода: " + first[:90]


def main():
    lines = [l for l in io.open(SCAN, encoding="utf-8").read().splitlines() if l.strip()]
    rows = []
    for line in lines:
        m = re.match(r"(T\d+)__(c\d)__(\d+): (.*)", line)
        t, c, i, rest = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        if rest.startswith("analyze"):
            mm = re.match(r"analyze \(\d+ issues\) (error|warning|info) - (.*)", rest)
            check = "analyze (%s)" % (mm.group(1) if mm else "issues")
            first = mm.group(2) if mm else rest
        else:
            check = rest.strip()
            first = rest
        cls, sub, note = classify(t, c, check, first)
        rows.append([t, c, i, cls, sub, note])
    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for r in rows:
            w.writerow(r)
    by_cfg_class = {}
    for t, c, i, cls, sub, note in rows:
        by_cfg_class.setdefault(c, {}).setdefault(cls, 0)
        by_cfg_class[c][cls] += 1
    print("строк:", len(rows))
    for c in sorted(by_cfg_class):
        print(" ", c, dict(sorted(by_cfg_class[c].items())))


if __name__ == "__main__":
    main()
