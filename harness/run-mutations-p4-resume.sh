#!/usr/bin/env bash
# Resume Phase 1.C P4 batch — only run skills that don't have a trace yet.
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

# Claude P4 (skip those already done)
for s in "${MUTATIONS[@]}"; do
  if [ -f "skills/$s/trace.json" ]; then
    echo "[resume] claude trace exists, skip: $s"
    continue
  fi
  echo "=========================================="
  echo "[resume] CLAUDE: $s"
  echo "=========================================="
  bash harness/run-skill.sh "$s" || echo "[resume] $s claude failed (continuing)"
  pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
  sleep 1
done

# Codex P4 (skip those already done)
for s in "${MUTATIONS[@]}"; do
  if [ -f "skills/$s/trace-codex.json" ]; then
    echo "[resume] codex trace exists, skip: $s"
    continue
  fi
  echo "=========================================="
  echo "[resume] CODEX: $s"
  echo "=========================================="
  bash harness/run-skill-codex.sh "$s" || echo "[resume] $s codex failed (continuing)"
  pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
  sleep 1
done

echo "=========================================="
echo "[resume] DONE"
echo "=========================================="
ls $PROJECT_ROOT/skills/zz-mutation-*/trace.json $PROJECT_ROOT/skills/zz-mutation-*/trace-codex.json 2>&1 | head -20
