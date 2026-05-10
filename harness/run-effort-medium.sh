#!/usr/bin/env bash
# Re-do the N effort sensitivity traces with effort=medium (the valid claude
# CLI value; default-effort was rejected by the CLI's effort flag validator).
# Saves to trace-n-medium.json.
set -euo pipefail
cd /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise

for s in wrangler semgrep firebase-hosting-basics; do
  if [ -f "skills/$s/trace-n-medium.json" ]; then
    echo "[N-medium] $s exists, skip"
    continue
  fi
  echo "=========================================="
  echo "[N-medium] $s effort=medium"
  echo "=========================================="
  EFFORT_OVERRIDE="medium" TRACE_SUFFIX="-n-medium" bash harness/run-skill-effort.sh "$s" || \
    echo "[N-medium] $s failed (continuing)"
  pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
  pkill -KILL -f "firebase-tools" 2>/dev/null || true
  sleep 2
done

echo "=========================================="
echo "[N-medium] DONE"
echo "=========================================="
ls /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise/skills/{wrangler,semgrep,firebase-hosting-basics}/trace-n-medium.json 2>&1
