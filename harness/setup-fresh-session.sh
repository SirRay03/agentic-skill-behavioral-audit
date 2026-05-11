#!/usr/bin/env bash
# Build a fully isolated environment for running fresh-session and cross-LLM
# predictions. Nothing under this directory references the main project's
# ~/.claude/ or ~/.codex/ state — the only carryovers are oauth credentials
# (so the agents can authenticate) and the SKILL.md texts (the input we
# explicitly want them to read).
#
# Layout produced under $FRESH (default /tmp/fresh-predictor-batch):
#   home-claude/.claude/.credentials.json     # claude oauth only
#   home-codex/.codex/{auth.json,...}         # codex oauth only
#   skills/<id>/SKILL.md                      # 25 skills, no other files
#   outputs/{claude-fresh,codex-fresh}/<id>/  # per-skill prediction outputs
#   predict-fresh.py                          # adapted predict.py
#   predict-codex.py                          # codex variant
set -euo pipefail

FRESH="${FRESH:-/tmp/fresh-predictor-batch}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

echo "[setup-fresh] FRESH=$FRESH"
echo "[setup-fresh] PROJECT_ROOT=$PROJECT_ROOT"

# Wipe and recreate
rm -rf "$FRESH"
mkdir -p "$FRESH"/{skills,outputs/claude-fresh,outputs/codex-fresh,home-claude/.claude,home-codex/.codex}

# === Claude oauth (minimal) ===
if [ -f "$HOME/.claude/.credentials.json" ]; then
  cp "$HOME/.claude/.credentials.json" "$FRESH/home-claude/.claude/.credentials.json"
  chmod 600 "$FRESH/home-claude/.claude/.credentials.json"
  echo "[setup-fresh] copied claude oauth"
else
  echo "[setup-fresh] WARN: claude credentials not found"
fi

# === Codex oauth (whatever its state shape is) ===
if [ -d "$HOME/.codex" ]; then
  cp -r "$HOME/.codex"/* "$FRESH/home-codex/.codex/" 2>/dev/null || true
  echo "[setup-fresh] copied codex state ($(ls "$FRESH/home-codex/.codex/" | wc -l) entries)"
else
  echo "[setup-fresh] WARN: codex state not found"
fi

# === Copy SKILL.md texts for the 25 production skills ===
# Skip *-aug (augmented variants share the same trace) and zz-* (synthetic).
count=0
for src in "$PROJECT_ROOT/skills"/*/; do
  name="$(basename "$src")"
  if [[ "$name" == *-aug || "$name" == zz-* ]]; then
    continue
  fi
  if [ ! -f "$src/SKILL.md" ]; then
    continue
  fi
  mkdir -p "$FRESH/skills/$name"
  cp "$src/SKILL.md" "$FRESH/skills/$name/SKILL.md"
  count=$((count + 1))
done
echo "[setup-fresh] copied $count SKILL.md files"

# === Copy predictor scripts ===
cp "$PROJECT_ROOT/harness/predict-fresh.py" "$FRESH/predict-fresh.py" 2>/dev/null || \
  echo "[setup-fresh] WARN: predict-fresh.py not yet authored — run setup again after authoring"
cp "$PROJECT_ROOT/harness/predict-codex.py" "$FRESH/predict-codex.py" 2>/dev/null || \
  echo "[setup-fresh] WARN: predict-codex.py not yet authored"

echo ""
echo "[setup-fresh] DONE."
ls "$FRESH"
