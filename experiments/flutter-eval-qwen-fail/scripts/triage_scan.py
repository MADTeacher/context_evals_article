# -*- coding: utf-8 -*-
"""Сканер триажа v2: точные чеки каждой задачи (как в accept/*.sh).
Пишет results/analysis/triage_scan2.txt; кэш triage_cache2.json."""
import csv
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
CACHE = os.path.join(RES, "analysis", "triage_cache2.json")
OUT = os.path.join(RES, "analysis", "triage_scan2.txt")


def grep_rc(pat, path, is_dir=True):
    p = subprocess.run(["grep", "-rnE", pat, path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.returncode == 0


def grep_count(pat, path):
    p = subprocess.run(["grep", "-cE", pat, path],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        return int((p.stdout or "0").strip())
    except ValueError:
        return 0


CHECKS = {
    "T1": lambda ws: [
        ("grep fetchRates", grep_rc("fetchRates", ws + "/lib/app/currency_list/")),
        ("grep USD", grep_rc("'USD'", ws + "/lib/app/currency_list/")),
        ("grep пагинация", grep_rc(r"hasMore|page \+ 1|page\+1", ws + "/lib/app/currency_list/")),
    ],
    "T2": lambda ws: [
        ("grep fetchRates", grep_rc("fetchRates", ws + "/lib/app/currency_list/")),
        ("grep USD", grep_rc("'USD'", ws + "/lib/app/currency_list/")),
        ("grep пагинация", grep_rc(r"hasMore|page \+ 1|page\+1", ws + "/lib/app/currency_list/")),
    ],
    "T3": lambda ws: [
        ("grep loadNewsFeed", grep_rc("loadNewsFeed", ws + "/lib/app/news_list/")),
        ("grep forceRefresh:true", grep_rc("forceRefresh: true", ws + "/lib/app/news_list/")),
    ],
    "T4": lambda ws: [
        ("grep loadNewsFeed>=2", grep_count("loadNewsFeed", ws + "/lib/app/news_list/news_list_page.dart") >= 2),
        ("grep forceRefresh:true", grep_rc("forceRefresh: true", ws + "/lib/app/news_list/")),
        ("grep forceRefresh:false|all", grep_rc(r"forceRefresh: false\|NewsFeedFilter.all", ws + "/lib/app/news_list/")),
    ],
    "T5": lambda ws: [
        ("grep readThemeMode(тест)", grep_rc("readThemeMode", ws + "/test/unit/repository_test.dart")),
        ("grep initAsyncData(тест)", grep_rc("initAsyncData", ws + "/test/unit/repository_test.dart")),
    ],
    "T6": lambda ws: [
        ("grep themeModeStream", grep_rc("themeModeStream", ws + "/lib/app/profile/")),
        ("grep readThemeMode", grep_rc("readThemeMode", ws + "/lib/app/profile/")),
    ],
    "T7": lambda ws: [
        ("grep fetchRates", grep_rc("fetchRates", ws + "/lib/app/")),
        ("grep loadNewsFeed", grep_rc("loadNewsFeed", ws + "/lib/app/")),
        ("changelog>=3", len([f for f in os.listdir(ws + "/changelog") if f.endswith(".rst")]) >= 3
            if os.path.isdir(ws + "/changelog") else False),
    ],
    "T8": lambda ws: [
        ("grep Future.wait", grep_rc("Future.wait", ws + "/lib/app/")),
        ("grep fetchRates", grep_rc("fetchRates", ws + "/lib/app/")),
        ("grep loadNewsFeed", grep_rc("loadNewsFeed", ws + "/lib/app/")),
        ("changelog>=3", len([f for f in os.listdir(ws + "/changelog") if f.endswith(".rst")]) >= 3
            if os.path.isdir(ws + "/changelog") else False),
    ],
}


def analyze(ws):
    try:
        p = subprocess.run(["flutter.bat", "analyze"], cwd=ws, text=True,
                           capture_output=True, timeout=180)
        out = p.stdout + p.stderr
        m = re.search(r"(\d+) issue", out)
        first = ""
        for line in out.splitlines():
            if "error -" in line or "warning -" in line:
                first = line.strip()[:140]
                break
            if "info -" in line and not first:
                first = line.strip()[:140]
        return "No issues found!" in out, (m.group(1) if m else "?"), first
    except Exception as e:
        return False, "ERR", "%s: %s" % (type(e).__name__, str(e)[:80])


def dep_used(ws):
    p = subprocess.run(["grep", "-rnE", r"\.getCurrencyList\(|\.getNewsList\(|\.themeMode\b",
                        ws + "/lib/app"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.returncode == 0


def tests(ws):
    try:
        p = subprocess.run(["flutter.bat", "test"], cwd=ws, text=True,
                           capture_output=True, timeout=420)
        out = (p.stdout + p.stderr).strip()
        if "All tests passed!" in out:
            return "tests: ВСЕ ЗЕЛЁНЫЕ (ложный отказ приёмки?)"
        m = re.findall(r"\[E\][^\n]{0,110}", out)
        return "tests: FAIL — " + (m[0] if m else out[-110:].replace("\n", " | "))
    except Exception as e:
        return "tests: ERR %s" % type(e).__name__


def main():
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(io.open(CACHE, encoding="utf-8"))
    fails = []
    with io.open(os.path.join(RES, "runs.csv"), encoding="utf-8", errors="replace", newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 15 and r[0].startswith("T") and r[3] == "0" and r[4] != "0":
                fails.append((r[0], r[1], int(r[2])))
    fails.sort()
    lines = []
    for t, c, i in fails:
        key = "%s__%s__%d" % (t, c, i)
        if key in cache:
            res = cache[key]
        else:
            ws = os.path.join(ROOT, "workspaces", "run", key)
            if not os.path.isdir(ws):
                res = {"check": "нет workspace"}
            else:
                res = {"check": "ok"}
                for name, passed in CHECKS[t](ws):
                    if not passed:
                        res = {"check": name}
                        break
                else:
                    ok, n, first = analyze(ws)
                    if not ok:
                        res = {"check": "analyze (%s issues)" % n, "first": first}
                    elif t != "T5" and dep_used(ws):
                        res = {"check": "deprecated-члены в lib/app"}
                    else:
                        res = {"check": tests(ws)}
            cache[key] = res
            json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        lines.append("%s: %s %s" % (key, res.get("check"), res.get("first", "")))
        sys.stdout.write(".")
        sys.stdout.flush()
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("\nготово: results/analysis/triage_scan2.txt (%d строк)" % len(lines))


if __name__ == "__main__":
    main()
