# -*- coding: utf-8 -*-
"""Проверка доступности API (прямой API DeepSeek): минимальный chat-completion.
Ключ читается из contexts/local-key.json эксперимента и НИКОГДА не печатается.
Код возврата 0 — API здоров, 1 — недоступен.
Использование: py scripts/api_health.py
"""
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYFILE = os.path.join(ROOT, "contexts", "local-key.json")
TEMPLATE = os.path.join(ROOT, "contexts", "config.template.json")


def main():
    key = json.load(io.open(KEYFILE, encoding="utf-8"))["api_key"]
    tpl = json.load(io.open(TEMPLATE, encoding="utf-8"))
    body = {
        "model": tpl["model"],
        "max_tokens": 200,
        "messages": [{"role": "user", "content": "Reply with the single word OK"}],
    }
    body.update(tpl.get("extra_body") or {})
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        tpl["base_url"].rstrip("/") + "/chat/completions",
        data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
            content = (d.get("choices") or [{}])[0].get("message", {}).get("content")
            print("api_health: HTTP %s, %s" % (r.status, "ok" if content else "пустой ответ"))
            return 0 if content else 1
    except urllib.error.HTTPError as e:
        print("api_health: HTTPError %s: %s" % (e.code, e.read()[:120]))
        return 1
    except Exception as e:
        print("api_health: %s: %s" % (type(e).__name__, str(e)[:120]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
