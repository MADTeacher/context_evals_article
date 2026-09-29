# -*- coding: utf-8 -*-
"""Анализ серии drift-eval: p̂ с ДИ Вильсона, навыки/V-хуки по трассам,
ресурсы, триаж-сигналы неудач. Пишет results/analysis/final-report-drift.md.
Классификация неудач — из results/analysis/triage.csv (T,C,I,class,subclass,note),
заполняется вручную по логам; при отсутствии файла в отчёт идёт таблица сигналов.
Использование: py scripts/analyze_drift.py
"""
import csv
import io
import json
import math
import os
import re
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
TASKS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
CONFIGS = ["c0", "c1", "c2"]
CLABEL = {"c0": "C0", "c1": "C1", "c2": "C2"}
GROUPS = [
    ("currency", ["T1", "T2"]),
    ("news", ["T3", "T4"]),
    ("settings", ["T5", "T6"]),
    ("mixed", ["T7", "T8"]),
]
V2_TASKS = ["T1", "T2", "T4", "T5", "T6"]  # задачи с конвенциями v2
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


def fmt_ci(k, n):
    if n == 0:
        return "—"
    p, lo, hi = wilson(k, n)
    return "%d/%d; %s [%s; %s]" % (k, n, pct(p), pct(lo), pct(hi))


def load_runs():
    rows = []
    with io.open(os.path.join(RES, "runs.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 15 and r[0].startswith("T"):
                rows.append({
                    "T": r[0], "C": r[1], "I": int(r[2]),
                    "rc": int(r[3]), "acc": int(r[4]),
                    "dur": int(r[7]), "turns_csv": int(r[8]),
                    "tin": int(r[9]), "tout": int(r[10]), "total": int(r[11]),
                    "blocked": int(r[12]), "skills_csv": r[13],
                })
    return rows


def load_trace(name):
    """Строгий парсинг JSONL: skill_activated (имя на верхнем уровне),
    hook_blocked, ходы = max(turn) по model_usage."""
    path = os.path.join(RES, "traces", name + ".jsonl")
    skills, blocked, turns, tin, tout, mig_contact = set(), 0, 0, 0, 0, False
    n_events = 0
    try:
        with io.open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                n_events += 1
                ev = e.get("event", "")
                if ev == "skill_activated":
                    skills.add(e.get("skill") or e.get("name") or "?")
                elif ev == "hook_blocked":
                    blocked += 1
                elif ev == "model_usage":
                    turns = max(turns, int(e.get("turn") or 0))
                    tin += int(e.get("prompt_tokens") or 0)
                    tout += int(e.get("completion_tokens") or 0)
                elif ev == "tool_observation":
                    if "migration-v2" in json.dumps(e, ensure_ascii=False):
                        mig_contact = True
    except OSError:
        return None
    return {"skills": skills, "blocked": blocked, "turns": turns,
            "tin": tin, "tout": tout, "mig": mig_contact, "events": n_events}


def log_signals(name):
    """Сигналы триажа из лога прогона."""
    path = os.path.join(RES, "logs", name + ".out")
    sig = {"deprecated": 0, "v1api": 0, "mig": 0, "tests_pass": False,
           "tests_fail": False, "analyze_ok": False, "bytes": 0}
    try:
        with io.open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return sig
    sig["bytes"] = len(text)
    sig["deprecated"] = len(re.findall(r"deprecated_member_use", text))
    sig["v1api"] = len(re.findall(r"getCurrencyList\(|getNewsList\(|\.themeMode\b", text))
    sig["mig"] = len(re.findall(r"migration-v2", text))
    tail = text[-200000:]
    sig["tests_pass"] = "All tests passed!" in tail
    sig["tests_fail"] = "Some tests failed" in tail
    sig["analyze_ok"] = "No issues found!" in tail
    return sig


def load_triage():
    path = os.path.join(RES, "analysis", "triage.csv")
    out = {}
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 5 and r[0].startswith("T"):
                out[(r[0], r[1], int(r[2]))] = {"class": r[3], "sub": r[4], "note": r[5] if len(r) > 5 else ""}
    return out


def main():
    runs = load_runs()
    for r in runs:
        r["trace"] = load_trace("%s__%s__%d" % (r["T"], r["C"], r["I"]))
        r["log"] = log_signals("%s__%s__%d" % (r["T"], r["C"], r["I"]))

    have = {(r["T"], r["C"], r["I"]) for r in runs}
    missing = [(t, c, i) for t in TASKS for c in CONFIGS for i in range(1, 6) if (t, c, i) not in have]
    unresolved = [r for r in runs if r["rc"] != 0 and r["acc"] != 0]
    no_trace = [r for r in runs if r["trace"] is None]

    def ok(r):
        return 1 if (r["rc"] == 0 and r["acc"] == 0) else 0

    def cell(task, c):
        rs = [r for r in runs if r["T"] == task and r["C"] == c]
        return sum(map(ok, rs)), len(rs)

    tri = load_triage()

    L = []
    w = L.append
    w("# Отчёт серии drift-eval (Flutter, API-drift) — deepseek/deepseek-v4.1-flash")
    w("")
    w("Методика protocol/methodology.md v1.1 (pre-registration): temperature 0,8,")
    w("max_turns 150, таймаут 1800 с, контекст 256 000, k=5. Полигон: lab_8 v3")
    w("(коммит ebf17f9, single-carrier: fetchRates с default-base (ловушка 'EUR'/конвенция")
    w("'USD' только в контексте C2), loadNewsFeed(NewsFeedFilter) с forceRefresh-семантикой,")
    w("readThemeMode() с init-guard; старые члены @Deprecated без текстов-подсказок;")
    w("docs/migration-v2.md удалён). Зонды: знаний — deepseek lab_8 не знает")
    w("(protocol/probe-result.md); выводимости — C0-агенты не сдают T1 (results/probe/).")
    w("")
    w("## 1. Целостность серии")
    w("")
    w("Комбинаций заполнено: %d/120; отсутствуют: %s; прогонов без трассы: %s;"
      " строк с rc≠0 и accept≠0 (флэки, после перезапусков должно быть 0): %d."
      % (len(have), ", ".join("/".join(map(str, m)) for m in missing) or "нет",
         ", ".join("%s__%s__%d" % (r["T"], r["C"], r["I"]) for r in no_trace) or "нет",
         len(unresolved)))
    w("")

    w("## 2. Успешность (p̂ с 95 % ДИ Вильсона)")
    w("")
    w("| Задача (группа) | C0 | C1 | C2 |")
    w("| --- | --- | --- | --- |")
    grp_of = {}
    for g, ts in GROUPS:
        for t in ts:
            grp_of[t] = g
    for t in TASKS:
        cells = [cell(t, c) for c in CONFIGS]
        w("| %s (%s) | %s | %s | %s |" % (
            t, grp_of[t],
            fmt_ci(*cells[0]), fmt_ci(*cells[1]), fmt_ci(*cells[2])))
    for g, ts in GROUPS:
        cells = []
        for c in CONFIGS:
            rs = [r for r in runs if r["T"] in ts and r["C"] == c]
            cells.append((sum(map(ok, rs)), len(rs)))
        w("| Группа %s | %s | %s | %s |" % (
            g, fmt_ci(*cells[0]), fmt_ci(*cells[1]), fmt_ci(*cells[2])))
    cells = []
    for c in CONFIGS:
        rs = [r for r in runs if r["C"] == c]
        cells.append((sum(map(ok, rs)), len(rs)))
    w("| **Итого** | %s | %s | %s |" % (fmt_ci(*cells[0]), fmt_ci(*cells[1]), fmt_ci(*cells[2])))
    w("")

    # Контрасты по группам задач
    w("### Контрасты (разность p̂)")
    w("")
    w("| Срез | C2 − C0 | C2 − C1 | C1 − C0 |")
    w("| --- | --- | --- | --- |")
    for label, ts in [("Всё", TASKS), ("Конвенции v2 (T1/T2/T4/T5/T6)", V2_TASKS)] + \
                     [(g, ts) for g, ts in GROUPS]:
        vals = []
        for a, b in [("c2", "c0"), ("c2", "c1"), ("c1", "c0")]:
            ra = [r for r in runs if r["T"] in ts and r["C"] == a]
            rb = [r for r in runs if r["T"] in ts and r["C"] == b]
            if not ra or not rb:
                vals.append(None)
            else:
                vals.append(sum(map(ok, ra)) / len(ra) - sum(map(ok, rb)) / len(rb))
        w("| %s | %s | %s | %s |" % (label,
                                     pct(vals[0]) if vals[0] is not None else "—",
                                     pct(vals[1]) if vals[1] is not None else "—",
                                     pct(vals[2]) if vals[2] is not None else "—"))
    w("")

    w("## 3. Ресурсы на прогон (средние по завершённым прогонам)")
    w("")
    w("| Конфигурация | Вх. токены | Исх. токены | Ходы | Длительность, с |")
    w("| --- | --- | --- | --- | --- |")
    for c in CONFIGS:
        rs = [r for r in runs if r["C"] == c and r["trace"]]
        if not rs:
            continue
        w("| %s | %s | %s | %s | %s |" % (
            CLABEL[c],
            "%.0f тыс." % (statistics.mean(r["trace"]["tin"] for r in rs) / 1000),
            "%.1f тыс." % (statistics.mean(r["trace"]["tout"] for r in rs) / 1000),
            "%.1f" % statistics.mean(r["trace"]["turns"] for r in rs),
            "%.0f" % statistics.mean(r["dur"] for r in rs)))
    w("")

    w("## 4. Активация навыков и V-хуки (строго по событиям трасс)")
    w("")
    w("| Конфигурация | Прогонов с ≥1 активацией | Навыки (активаций) | Прогонов с блокировками | Блокировок всего |")
    w("| --- | --- | --- | --- | --- |")
    for c in CONFIGS:
        rs = [r for r in runs if r["C"] == c and r["trace"]]
        act = [r for r in rs if r["trace"]["skills"]]
        cnt = {}
        for r in act:
            for s in r["trace"]["skills"]:
                cnt[s] = cnt.get(s, 0) + 1
        blocked_runs = [r for r in rs if r["trace"]["blocked"] > 0]
        w("| %s | %d/%d | %s | %d | %d |" % (
            CLABEL[c], len(act), len(rs),
            ", ".join("%s (%d)" % kv for kv in sorted(cnt.items())) or "—",
            len(blocked_runs), sum(r["trace"]["blocked"] for r in rs)))
    w("")
    mig_reads = {}
    for c in CONFIGS:
        rs = [r for r in runs if r["C"] == c and r["trace"]]
        mig_reads[c] = sum(1 for r in rs if r["trace"]["mig"] or r["log"]["mig"] > 0)
    w("Контакт с docs/migration-v2.md (упоминание в трассе или логе): " +
      ", ".join("%s — %d/%d" % (CLABEL[c], mig_reads[c],
                                len([r for r in runs if r["C"] == c])) for c in CONFIGS) + ".")
    w("")

    w("## 5. Триаж неудач")
    w("")
    fails = [r for r in runs if not ok(r)]
    w("Неудач (rc≠0 или accept≠0): %d." % len(fails))
    if fails:
        w("")
        w("| Прогон | rc/accept | ходы | сигналы лога (deprecated / v1-API / migration-v2 / тесты / analyze) | класс |")
        w("| --- | --- | --- | --- | --- |")
        for r in sorted(fails, key=lambda x: (x["T"], x["C"], x["I"])):
            name = "%s__%s__%d" % (r["T"], r["C"], r["I"])
            s = r["log"]
            t = r["trace"] or {}
            tests = "ok" if s["tests_pass"] else ("падают" if s["tests_fail"] else "нет запуска")
            an = "ok" if s["analyze_ok"] else "есть замечания"
            tr = tri.get((r["T"], r["C"], r["I"]), {})
            cls = tr.get("class", "?")
            w("| %s | %d/%d | %s | %d / %d / %d / %s / %s | %s |" % (
                name, r["rc"], r["acc"], t.get("turns", "?"),
                s["deprecated"], s["v1api"], s["mig"], tests, an, cls))
        w("")
        classified = [tri[k] for k in tri]
        by = {}
        for v in classified:
            by[v["class"]] = by.get(v["class"], 0) + 1
        if by:
            total = sum(by.values())
            parts = ", ".join("(%s) — %d" % kv for kv in sorted(by.items()))
            w("Классификация (%d из %d): %s." % (total, len(fails), parts))
            q = {
                c: (
                    sum(1 for k, v in tri.items() if v["class"] == "1" and k[1] == c),
                    len([r for r in fails if r["C"] == c]),
                )
                for c in CONFIGS
            }
            w("Доля класса (1) q_C: " + ", ".join(
                "%s — %d из %d неудач" % (CLABEL[c], v[0], v[1]) if v[1] else "%s — неудач нет" % CLABEL[c]
                for c, v in q.items()) + ".")
        else:
            w("Классификация не заполнена (results/analysis/triage.csv отсутствует/пуст).")
    w("")
    w("Легенда классов: (1) дефект контекста — конвенция v2 не сообщена контекстом;"
      " (2) ограничение модели-среды, включая подкласс stale-knowledge (агент применил")
    w("несуществующий или @Deprecated API); (3) флейк среды.")
    w("")

    out_dir = os.path.join(RES, "analysis")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    out = os.path.join(out_dir, "final-report-drift.md")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print("написан %s" % out)
    print("комбинаций: %d/120, неудач: %d, флэков (rc!=0 и accept!=0): %d"
          % (len(have), len(fails), len(unresolved)))
    for c in CONFIGS:
        rs = [r for r in runs if r["C"] == c]
        print("  %s: %d/%d ok" % (CLABEL[c], sum(map(ok, rs)), len(rs)))


if __name__ == "__main__":
    main()
