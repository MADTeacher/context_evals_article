# -*- coding: utf-8 -*-
"""Одна строка CSV по JSONL-трассе прогона madharness-mini."""
import io
import json
import sys


def main() -> None:
    s, c, i, rc, acc, archv, navv, dur, trace = sys.argv[1:10]
    tin = tout = turns = blocked = 0
    skills = set()
    status = ""
    if trace != "none":
        try:
            events = [
                json.loads(line)
                for line in io.open(trace, encoding="utf-8").read().splitlines()
                if line.strip()
            ]
        except OSError:
            events = []
        for e in events:
            ev = e.get("event", "")
            if ev == "model_usage":
                tin += int(e.get("prompt_tokens") or 0)
                tout += int(e.get("completion_tokens") or 0)
            elif ev == "skill_activated":
                skills.add(e.get("skill") or e.get("name") or "?")
            elif ev == "hook_blocked":
                blocked += 1
            elif ev == "session_end":
                pass
                if not status:
                    status = str(e.get("result", ""))[:80]
    row = [
        s, c, i, rc, acc, archv, navv, dur,
        turns, tin, tout, tin + tout, blocked,
        ";".join(sorted(skills)),
        '"' + status.replace('"', "'") + '"',
    ]
    sys.stdout.write(",".join(str(x) for x in row) + "\n")


if __name__ == "__main__":
    main()
