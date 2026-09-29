#!/usr/bin/env bash
# Собрать референсные workspace конфигурации c0/c1/c2 из fixture (v2) + контексты.
# Использование: make_workspace.sh <c0|c1|c2>
set -euo pipefail
C="${1:?c0|c1|c2}"
ROOT="/c/Users/MADTeacher/Documents/GitHub/flutter-drift-eval-qwen"
KEYFILE="/c/Users/MADTeacher/Documents/GitHub/flutter-drift-eval-qwen/contexts/local-key.json"

rm -rf "$ROOT/workspaces/$C"
mkdir -p "$ROOT/workspaces"
cp -r "$ROOT/fixture" "$ROOT/workspaces/$C"
rm -rf "$ROOT/workspaces/$C/.git" "$ROOT/workspaces/$C/build" "$ROOT/workspaces/$C/.dart_tool"
cd "$ROOT/workspaces/$C"

py - "$ROOT" "$KEYFILE" <<'PYEOF'
import json, io, os, sys
root, keyfile = sys.argv[1], sys.argv[2]
tpl = io.open(root + r"\contexts\config.template.json", encoding="utf-8").read()
key = json.load(io.open(keyfile, encoding="utf-8"))["api_key"]
cfg = tpl.replace("__API_KEY__", key)
os.makedirs(".madharness-mini", exist_ok=True)
io.open(".madharness-mini/config.json", "w", encoding="utf-8", newline="\n").write(cfg)
PYEOF

case "$C" in
  c0)
    ;;
  c1)
    cp "$ROOT/contexts/c1/AGENTS.md" ./AGENTS.md
    mkdir -p .agents/skills
    cp -r "$ROOT/skills-src/"*/ .agents/skills/
    ;;
  c2)
    cp "$ROOT/contexts/c2/AGENTS.md" ./AGENTS.md
    cp "$ROOT/contexts/c2/app/AGENTS.md" ./lib/app/AGENTS.md
    cp "$ROOT/contexts/c2/data/AGENTS.md" ./lib/data/AGENTS.md
    cp "$ROOT/contexts/c2/domain/AGENTS.md" ./lib/domain/AGENTS.md
    mkdir -p .agents/skills scripts/hooks
    cp -r "$ROOT/contexts/c2/skills/migration-v2" .agents/skills/
    cp -r "$ROOT/skills-src/flutter-testing" .agents/skills/
    cp "$ROOT/contexts/c2/hooks/hooks.json" .madharness-mini/hooks.json
    cp "$ROOT/contexts/c2/scripts/hooks/guard_v2.py" scripts/hooks/guard_v2.py
    ;;
  *) echo "unknown config: $C"; exit 99 ;;
esac
echo "workspace $C готов"
