#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for s in zz-mutation-1-obfuscated-curl \
         zz-mutation-2-dns-exfil \
         zz-mutation-3-webfetch-indirection \
         zz-mutation-4-bundled-sibling \
         zz-mutation-5-time-bombed \
         zz-mutation-6-dependency-confusion; do
  mkdir -p "$HOME/.claude/skills/$s"
  cp "$PROJECT_ROOT/skills/$s/SKILL.md" "$HOME/.claude/skills/$s/"
  if [ -d "$PROJECT_ROOT/skills/$s/references" ]; then
    cp -r "$PROJECT_ROOT/skills/$s/references" "$HOME/.claude/skills/$s/"
  fi
  echo "installed $s"
done
ls "$HOME/.claude/skills/" | grep zz-mutation
