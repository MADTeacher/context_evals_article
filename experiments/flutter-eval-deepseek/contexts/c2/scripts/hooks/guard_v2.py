"""V-хуки C2 (drift v2): запрет @Deprecated-членов в lib/**, защита контекста,
запрет деструктивных git-команд. Событие harness читается из stdin."""
import json
import re
import sys

PROTECTED = re.compile(
    r"^(AGENTS\.md$|\.agents/|\.madharness-mini/)"
)
DEPRECATED = re.compile(r"\.getCurrencyList\(|\.getNewsList\(|\.themeMode\b")
DESTRUCTIVE = re.compile(
    r"\bgit +(commit|push|reset|clean|rebase|merge)\b|\bgit +checkout +--\b|\brm +-rf\b"
)
REPLACEMENT = (
    "Нарушение контракта миграции v2 (навык migration-v2): "
    "курс — fetchRates(CurrencyPageRequest(base: 'USD', ...)); "
    "лента — loadNewsFeed(NewsFeedFilter) с forceRefresh по семантике свежести; "
    "режим темы — readThemeMode() после initAsyncData()."
)


def main() -> None:
    event = json.load(sys.stdin)
    data = event.get("data", {})
    tool = data.get("tool", "")
    args = data.get("args", {}) or {}

    if tool in ("write_file", "apply_patch"):
        path = (args.get("path") or args.get("file") or "").replace("\\", "/")
        if PROTECTED.match(path):
            print(json.dumps({
                "ok": False,
                "block": f"Защита контекста: '{path}' — часть контекстной конфигурации "
                         f"и не изменяется агентом.",
            }))
            return
        if path.startswith("lib/"):
            text = args.get("content") or args.get("new_string") or ""
            if DEPRECATED.search(text):
                print(json.dumps({"ok": False, "block": REPLACEMENT}))
                return

    if tool == "run_shell":
        cmd = args.get("command") or " ".join(args.get("cmd", []))
        if DESTRUCTIVE.search(cmd):
            print(json.dumps({
                "ok": False,
                "block": f"Запрещённая команда: '{cmd}'. Рабочая копия неизменяема "
                         f"как целое; изменения вносятся правкой файлов.",
            }))
            return

    print(json.dumps({"ok": True}))


if __name__ == "__main__":
    main()
