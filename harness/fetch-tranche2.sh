#!/usr/bin/env bash
# Fetch SKILL.md for the 10 tranche-2 skills (n=15 → n=25 expansion, 2026-05-09).
# Run from the project root.
set -euo pipefail

declare -A SKILLS=(
  [cloudformation]="itsmostafa/aws-agent-skills/main/skills/cloudformation/SKILL.md"
  [pinecone-mcp]="pinecone-io/skills/main/skills/pinecone-mcp/SKILL.md"
  [prompt-images]="replicate/skills/main/skills/prompt-images/SKILL.md"
  [prisma-postgres-setup]="prisma/skills/main/prisma-postgres-setup/SKILL.md"
  [auth0-quickstart]="auth0/agent-skills/main/plugins/auth0/skills/auth0-quickstart/SKILL.md"
  [sentry-setup-ai-monitoring]="getsentry/sentry-agent-skills/main/skills/sentry-setup-ai-monitoring/SKILL.md"
  [gha-security-review]="getsentry/skills/main/skills/gha-security-review/SKILL.md"
  [semgrep]="semgrep/skills/main/skills/semgrep/SKILL.md"
  [vercel-sandbox]="vercel-labs/agent-browser/main/skill-data/vercel-sandbox/SKILL.md"
  [xcode-project-setup]="firebase/agent-skills/main/skills/xcode-project-setup/SKILL.md"
)

for id in "${!SKILLS[@]}"; do
  path="${SKILLS[$id]}"
  url="https://raw.githubusercontent.com/$path"
  out="skills/$id/SKILL.md"
  mkdir -p "skills/$id"
  printf 'fetching %s ... ' "$id"
  if curl -fsSL "$url" -o "$out"; then
    printf '%s lines\n' "$(wc -l < "$out")"
  else
    printf 'FAILED (%s)\n' "$url"
  fi
done
