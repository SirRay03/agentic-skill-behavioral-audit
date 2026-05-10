#!/usr/bin/env bash
# Phase 1.E — Cross-agent dynamic on 5 more skills via Codex CLI.
set -euo pipefail

cd /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise

for s in agent-browser firebase-hosting-basics semgrep cookie-sync find-skills; do
  echo "=========================================="
  echo "[run-codex-batch] starting $s"
  echo "=========================================="
  bash harness/run-skill-codex.sh "$s" || echo "[run-codex-batch] $s failed (continuing)"
  echo
done

echo "=========================================="
echo "[run-codex-batch] DONE"
echo "=========================================="
ls skills/agent-browser/trace-codex.json skills/firebase-hosting-basics/trace-codex.json \
   skills/semgrep/trace-codex.json skills/cookie-sync/trace-codex.json \
   skills/find-skills/trace-codex.json 2>&1
