# -*- coding: utf-8 -*-
"""Сканер утечек конвенций v2 (методика v1.1, §2а): конвенции дрейфа не должны
присутствовать в фикстуре (код/тесты/changelog/assets) и в текстах сценариев —
единственный носитель — контекст C2. Отчёт advisory: 'USD' в мок-данных списка
(символ валюты) — не утечка request-конвенции, разбирается вручную.
Использование: py scripts/leak_scan.py  — rc=1, если найдена утечка класса request."""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    ("fixture", ["lib", "test", "changelog", "assets"]),
]
SCEN = os.path.join(ROOT, "protocol", "scenarios")

# Маркеры request-конвенции (жёсткие) и мягкие (совпадения к ручному разбору).
HARD = [
    re.compile(r"base\s*:\s*['\"]USD['\"]"),      # base-конвенция в запросе
    re.compile(r"CurrencyPageRequest\(base"),     # явный base в любом запросе
    re.compile(r"docs/migration-v2"),             # указатели на удалённую доку
    re.compile(r"используйте (fetchRates|loadNewsFeed|readThemeMode)"),  # шимы-подсказки
]
SOFT = [
    re.compile(r"['\"]USD['\"]"),                 # символ в данных/тестах — разобрать
    re.compile(r"forceRefresh:\s*(true|false)"),  # образец флага в lib/app
    re.compile(r"(?i)cache-then-network"),        # семантика в changelog/сценарии
]


def scan():
    leaks, soft = [], []
    for base, dirs in TARGETS:
        for d in dirs:
            p = os.path.join(ROOT, base, d)
            for dp, _, fns in os.walk(p):
                for fn in fns:
                    fp = os.path.join(dp, fn)
                    rel = os.path.relpath(fp, ROOT)
                    try:
                        text = io.open(fp, encoding="utf-8", errors="replace").read()
                    except OSError:
                        continue
                    for ln, line in enumerate(text.splitlines(), 1):
                        for rx in HARD:
                            if rx.search(line):
                                leaks.append("%s:%d: %s  [%s]" % (rel, ln, line.strip()[:90], rx.pattern[:30]))
                        for rx in SOFT:
                            if rx.search(line):
                                soft.append("%s:%d: %s  [%s]" % (rel, ln, line.strip()[:90], rx.pattern[:30]))
    for fn in sorted(os.listdir(SCEN)):
        fp = os.path.join(SCEN, fn)
        for ln, line in enumerate(io.open(fp, encoding="utf-8", errors="replace").read().splitlines(), 1):
            if re.search(r"USD|forceRefresh", line):
                leaks.append("protocol/scenarios/%s:%d: %s" % (fn, ln, line.strip()[:90]))
    print("=== утечки request-конвенций (жёсткие) ===")
    print("\n".join(leaks) if leaks else "нет")
    print("=== мягкие совпадения (ручной разбор) ===")
    print("\n".join(soft if soft else ["нет"]))
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(scan())
