#!/usr/bin/env bash
# Phase 3.L — Multi-task fuzzing.
# For each of 3 skills (wrangler, semgrep, firebase-hosting-basics), run two
# alternate task.md prompts (drawn from each maker's documentation).
# Saves to trace-l-alt1.json, trace-l-alt2.json.
set -euo pipefail
cd /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise

SKILLS=(wrangler semgrep firebase-hosting-basics)
ALTS=(alt1 alt2)

for s in "${SKILLS[@]}"; do
  for alt in "${ALTS[@]}"; do
    if [ -f "skills/$s/trace-l-${alt}.json" ]; then
      echo "[L-multitask] $s $alt trace exists, skip"
      continue
    fi
    echo "=========================================="
    echo "[L-multitask] $s ($alt)"
    echo "=========================================="

    # Swap in the alternate task.md temporarily, run, then restore
    cp "skills/$s/task.md" "skills/$s/task.md.bak"
    cp "skills/$s/multi-task/task-${alt}.md" "skills/$s/task.md"

    TRACE_SUFFIX="-l-${alt}" bash harness/run-skill.sh "$s" || \
      echo "[L-multitask] $s $alt failed (continuing)"

    # Restore original task.md
    mv "skills/$s/task.md.bak" "skills/$s/task.md"
    pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
    sleep 2
  done
done

echo "=========================================="
echo "[L-multitask] DONE"
echo "=========================================="
ls /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise/skills/{wrangler,semgrep,firebase-hosting-basics}/trace-l-*.json 2>&1 | head -10
