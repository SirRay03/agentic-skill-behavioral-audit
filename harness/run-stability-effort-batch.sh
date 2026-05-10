#!/usr/bin/env bash
# Phase 3.K + 3.N — repeat-invocation stability + runtime effort sensitivity.
# Runs the same harness with different TRACE_SUFFIX values to save outputs to
# distinct paths so existing traces aren't clobbered.
set -euo pipefail
cd /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise

# --- Phase 3.K: repeat-invocation stability ---
# 3 skills × 2 additional reps each at the default high-effort, alongside the
# existing trace.json as rep0. Saves to trace-k-rep1.json, trace-k-rep2.json.

K_SKILLS=(wrangler semgrep agent-browser)
for s in "${K_SKILLS[@]}"; do
  for rep in 1 2; do
    if [ -f "skills/$s/trace-k-rep${rep}.json" ]; then
      echo "[K-$s-rep${rep}] trace exists, skip"
      continue
    fi
    echo "=========================================="
    echo "[K-stability] $s rep $rep (effort=high)"
    echo "=========================================="
    TRACE_SUFFIX="-k-rep${rep}" bash harness/run-skill.sh "$s" || \
      echo "[K-stability] $s rep $rep failed (continuing)"
    pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
    sleep 2
  done
done

# --- Phase 3.N: runtime effort sensitivity ---
# 3 skills × 2 additional efforts (default + xhigh), the existing trace.json
# already provides the high-effort point.

N_SKILLS=(wrangler semgrep firebase-hosting-basics)
N_EFFORTS=(default xhigh)

for s in "${N_SKILLS[@]}"; do
  for effort in "${N_EFFORTS[@]}"; do
    if [ -f "skills/$s/trace-n-${effort}.json" ]; then
      echo "[N-$s-${effort}] trace exists, skip"
      continue
    fi
    echo "=========================================="
    echo "[N-effort] $s effort=${effort}"
    echo "=========================================="
    # We need to override the --effort flag inside run-skill.sh. Patch via
    # a temporary override script that replaces the effort value at runtime.
    EFFORT_OVERRIDE="$effort" TRACE_SUFFIX="-n-${effort}" bash harness/run-skill-effort.sh "$s" || \
      echo "[N-effort] $s ${effort} failed (continuing)"
    pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
    sleep 2
  done
done

echo "=========================================="
echo "[stability-effort-batch] DONE"
echo "=========================================="
ls /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise/skills/{wrangler,semgrep,agent-browser,firebase-hosting-basics}/trace-{k-rep1,k-rep2,n-default,n-xhigh}.json 2>&1 | head -20
