#!/usr/bin/env bash
# Move the fresh-Claude + Codex predictions from /tmp/fresh-predictor-batch/ into the
# repo at skills/<id>/prediction-{fresh,codex}.json so Section 4 + 5.5 of the
# report cite reproducible files rather than ephemeral /tmp paths.
set -euo pipefail
cd /mnt/c/Users/RaySi/Documents/LatentSpace/kth-skill-audit-exercise

FRESH_ROOT=/tmp/fresh-predictor-batch

count=0
for src in "$FRESH_ROOT/outputs/claude-fresh"/*/prediction-fresh.json; do
  [ -f "$src" ] || continue
  sid=$(basename "$(dirname "$src")")
  dst="skills/$sid/prediction-fresh.json"
  if [ -d "skills/$sid" ]; then
    cp "$src" "$dst"
    count=$((count + 1))
  else
    echo "[skip] no skill dir: $sid"
  fi
done
echo "[fresh] copied $count predictions"

count=0
for src in "$FRESH_ROOT/outputs/codex-fresh"/*/prediction-codex.json; do
  [ -f "$src" ] || continue
  sid=$(basename "$(dirname "$src")")
  dst="skills/$sid/prediction-codex.json"
  if [ -d "skills/$sid" ]; then
    cp "$src" "$dst"
    count=$((count + 1))
  else
    echo "[skip] no skill dir: $sid"
  fi
done
echo "[codex] copied $count predictions"

echo "[verify] sample:"
ls -la skills/wrangler/prediction-{fresh,codex}.json skills/semgrep/prediction-{fresh,codex}.json 2>&1 | head -8
