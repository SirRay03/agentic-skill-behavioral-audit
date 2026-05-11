#!/usr/bin/env bash
# Run all 15 skills sequentially. Logs per-skill status to harness/run-all.log.
# Stops on first failure unless --continue-on-error is set.
#
# Usage:
#   run-all.sh                    # run all 15
#   run-all.sh --only web-search  # run a single skill (validation gate)
#   run-all.sh --continue-on-error  # don't stop on individual failures
set -uo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
HARNESS="$PROJECT_ROOT/harness"
LOG="$HARNESS/run-all.log"

ALL_SKILLS=(
  frontend-design
  skill-creator
  react-best-practices
  web-search
  firecrawl-scrape
  agent-browser
  firebase-hosting-basics
  wrangler
  azure-validate
  find-skills
  grill-me
  improve-codebase-architecture
  firebase-security-rules-auditor
  cookie-sync
  caveman
)

CONTINUE_ON_ERROR=0
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --continue-on-error) CONTINUE_ON_ERROR=1; shift ;;
    --only) ONLY="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [ -n "$ONLY" ]; then
  SKILLS=("$ONLY")
else
  SKILLS=("${ALL_SKILLS[@]}")
fi

: > "$LOG"
echo "[run-all] $(date -u +%FT%TZ) starting ${#SKILLS[@]} skill(s)" | tee -a "$LOG"

PASS=0
FAIL=0
SKIP=0
for skill in "${SKILLS[@]}"; do
  TRACE="${PROJECT_ROOT:-$PROJECT_ROOT}/skills/$skill/trace.json"
  if [ -f "$TRACE" ] && [ -z "$ONLY" ]; then
    echo "[run-all] SKIP $skill (trace.json exists — delete it to re-run)" | tee -a "$LOG"
    SKIP=$((SKIP + 1))
    continue
  fi
  echo "[run-all] >>> $skill" | tee -a "$LOG"
  if "$HARNESS/run-skill.sh" "$skill" 2>&1 | tee -a "$LOG"; then
    echo "[run-all] PASS $skill" | tee -a "$LOG"
    PASS=$((PASS + 1))
  else
    echo "[run-all] FAIL $skill (exit=$?)" | tee -a "$LOG"
    FAIL=$((FAIL + 1))
    if [ "$CONTINUE_ON_ERROR" -eq 0 ]; then
      echo "[run-all] stopping on first failure (use --continue-on-error to override)" | tee -a "$LOG"
      break
    fi
  fi
  echo "" | tee -a "$LOG"
done

echo "[run-all] $(date -u +%FT%TZ) done. PASS=$PASS FAIL=$FAIL SKIP=$SKIP" | tee -a "$LOG"
exit $FAIL
