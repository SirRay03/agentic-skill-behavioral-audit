#!/usr/bin/env bash
# Copy the 3 worst-F1 skills to *-aug dirs and append observed-but-undeclared
# hosts/paths to a new "Observed Network Endpoints" section in SKILL.md.
# Used by Enrichment 3 (augmented SKILL.md inverse experiment).
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

for s in wrangler firebase-hosting-basics semgrep; do
  src="$PROJECT_ROOT/skills/$s"
  dst="$PROJECT_ROOT/skills/${s}-aug"
  mkdir -p "$dst"
  cp "$src/SKILL.md" "$dst/SKILL.md"
  echo "copied $src/SKILL.md -> $dst/SKILL.md"
done
