# -*- coding: utf-8 -*-
"""Проверка доступности LLM API: минимальный chat-completion по форме конфига
эксперимента. Ключ читается из keyfile и НИКОГДА не печатается.
Использование: py api_health.py <config.template.json> <keyfile.json>
  config.template.json — JSON с полями model, base_url, temperature?, extra_body?
  keyfile.json         — JSON с полем api_key
Код возврата 0 — API здоров, 1 — недоступен.
"""
import io
import json
import sys
import urllib.error
import urllib.request


def main():
    tpl_path, key_path = sys.argv[1], sys.argv[2]
    tpl = json.load(io.open(tpl_path, encoding="utf-8"))
    key = json.load(io.open(key_path, encoding="utf-8"))["api_key"]
    body = {
        "model": tpl["model"],
        "max_tokens": 200,
        "messages": [{"role": "user", "content": "Reply with the single word OK"}],
    }
    body.update(tpl.get("extra_body") or {})
    req = urllib.request.Request(
        tpl["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
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
