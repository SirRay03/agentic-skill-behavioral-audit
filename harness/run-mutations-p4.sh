#!/usr/bin/env bash
# Run claude P4 + codex P4 on the 6 mutation variants.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MUTATIONS=(
  zz-mutation-1-obfuscated-curl
  zz-mutation-2-dns-exfil
  zz-mutation-3-webfetch-indirection
  zz-mutation-4-bundled-sibling
  zz-mutation-5-time-bombed
  zz-mutation-6-dependency-confusion
)

for s in "${MUTATIONS[@]}"; do
  echo "=========================================="
  echo "[mutations-p4] CLAUDE: $s"
  echo "=========================================="
  bash harness/run-skill.sh "$s" || echo "[mutations-p4] $s claude failed (continuing)"
  pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
  sleep 1
  echo
done

for s in "${MUTATIONS[@]}"; do
  echo "=========================================="
  echo "[mutations-p4] CODEX: $s"
  echo "=========================================="
  bash harness/run-skill-codex.sh "$s" || echo "[mutations-p4] $s codex failed (continuing)"
  pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
  sleep 1
  echo
done

echo "=========================================="
echo "[mutations-p4] DONE"
echo "=========================================="
ls $PROJECT_ROOT/skills/zz-mutation-*/trace.json $PROJECT_ROOT/skills/zz-mutation-*/trace-codex.json 2>&1
