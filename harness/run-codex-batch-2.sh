#!/usr/bin/env bash
# Phase 1.E continuation — codex P4 on remaining 4 skills.
# (agent-browser already done in batch-1)
set -euo pipefail

cd /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise

for s in semgrep find-skills cookie-sync firebase-hosting-basics; do
  echo "=========================================="
  echo "[run-codex-batch-2] starting $s"
  echo "=========================================="
  bash harness/run-skill-codex.sh "$s" || echo "[run-codex-batch-2] $s failed (continuing)"
  # Belt-and-braces orphan cleanup between runs
  pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
  pkill -KILL -f "firebase-tools" 2>/dev/null || true
  pkill -KILL -f "puppeteer" 2>/dev/null || true
  sleep 2
  echo
done

echo "=========================================="
echo "[run-codex-batch-2] DONE"
echo "=========================================="
ls /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise/skills/{agent-browser,firebase-hosting-basics,semgrep,cookie-sync,find-skills}/trace-codex.json 2>&1
