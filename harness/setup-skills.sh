#!/usr/bin/env bash
# Pre-install all 15 skills + their per-skill toolchains in WSL2 kali.
# Run once before the validation gate.
#
# Skills are placed under ~/.claude/skills/<id>/ so claude picks them up.
# Per-skill CLIs (firecrawl, wrangler, firebase-tools, agent-browser, belt) are
# installed via npm to a user-level prefix, no sudo needed.
#
# Usage:  bash harness/setup-skills.sh
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SKILLS_DIR="$HOME/.claude/skills"
CLONE_DIR="$HOME/.cache/monperrus-skill-sources"
NPM_PREFIX="$HOME/.npm-global"

mkdir -p "$SKILLS_DIR" "$CLONE_DIR" "$NPM_PREFIX"

# Configure npm to install globals to user dir (no sudo needed)
npm config set prefix "$NPM_PREFIX"
export PATH="$NPM_PREFIX/bin:$PATH"
if ! grep -q "npm-global/bin" "$HOME/.bashrc" 2>/dev/null; then
  echo "export PATH=\"$NPM_PREFIX/bin:\$PATH\"" >> "$HOME/.bashrc"
fi

echo "============================================================"
echo "[setup] npm global prefix: $NPM_PREFIX"
echo "[setup] python3 deps: scapy"
echo "============================================================"
pip3 install --user --quiet scapy 2>&1 | tail -3 || echo "[setup] pip install scapy failed — install manually if needed"

# skill_id|owner/repo|in-repo path
SKILL_MANIFEST=$(cat <<'EOF'
frontend-design|anthropics/skills|skills/frontend-design
skill-creator|anthropics/skills|skills/skill-creator
react-best-practices|vercel-labs/agent-skills|skills/react-best-practices
web-search|inference-skills/skills|tools/llm/web-search
firecrawl-scrape|firecrawl/cli|skills/firecrawl-scrape
agent-browser|vercel-labs/agent-browser|skills/agent-browser
firebase-hosting-basics|firebase/agent-skills|skills/firebase-hosting-basics
wrangler|cloudflare/skills|skills/wrangler
azure-validate|microsoft/azure-skills|skills/azure-validate
find-skills|vercel-labs/skills|skills/find-skills
grill-me|mattpocock/skills|skills/productivity/grill-me
improve-codebase-architecture|mattpocock/skills|skills/engineering/improve-codebase-architecture
firebase-security-rules-auditor|firebase/agent-skills|skills/firebase-security-rules-auditor
cookie-sync|browserbase/skills|skills/cookie-sync
caveman|juliusbrussee/caveman|caveman
cloudformation|itsmostafa/aws-agent-skills|skills/cloudformation
pinecone-mcp|pinecone-io/skills|skills/pinecone-mcp
prompt-images|replicate/skills|skills/prompt-images
prisma-postgres-setup|prisma/skills|prisma-postgres-setup
auth0-quickstart|auth0/agent-skills|plugins/auth0/skills/auth0-quickstart
sentry-setup-ai-monitoring|getsentry/sentry-agent-skills|skills/sentry-setup-ai-monitoring
gha-security-review|getsentry/skills|skills/gha-security-review
semgrep|semgrep/skills|skills/semgrep
vercel-sandbox|vercel-labs/agent-browser|skill-data/vercel-sandbox
xcode-project-setup|firebase/agent-skills|skills/xcode-project-setup
EOF
)

echo
echo "============================================================"
echo "[setup] cloning sources + placing SKILL.md trees"
echo "============================================================"

while IFS='|' read -r skill_id repo path; do
  [ -z "$skill_id" ] && continue
  echo "[setup] $skill_id  ($repo / $path)"

  # Clone repo to cache if not already there
  REPO_DIR="$CLONE_DIR/$repo"
  if [ ! -d "$REPO_DIR" ]; then
    mkdir -p "$(dirname "$REPO_DIR")"
    git clone --depth 1 --quiet "https://github.com/$repo" "$REPO_DIR" 2>&1 | tail -3
  fi

  TARGET="$SKILLS_DIR/$skill_id"
  rm -rf "$TARGET"
  cp -r "$REPO_DIR/$path" "$TARGET"
  echo "  installed -> $TARGET"
done <<< "$SKILL_MANIFEST"

echo
echo "============================================================"
echo "[setup] per-skill toolchains (npm globals to ~/.npm-global)"
echo "============================================================"

# firecrawl CLI
echo "[setup] firecrawl..."
npm install -g firecrawl 2>&1 | tail -3 || echo "  WARN: firecrawl install failed"

# wrangler (Cloudflare Workers CLI)
echo "[setup] wrangler..."
npm install -g wrangler@latest 2>&1 | tail -3 || echo "  WARN: wrangler install failed"

# firebase-tools (Firebase CLI)
echo "[setup] firebase-tools..."
npm install -g firebase-tools 2>&1 | tail -3 || echo "  WARN: firebase-tools install failed"

# agent-browser (heavy: pulls Chromium)
echo "[setup] agent-browser..."
npm install -g agent-browser 2>&1 | tail -3 || echo "  WARN: agent-browser install failed"
if command -v agent-browser >/dev/null 2>&1; then
  agent-browser install 2>&1 | tail -3 || echo "  WARN: agent-browser install (browser binary) failed"
else
  echo "  WARN: agent-browser binary not on PATH after install"
fi

# belt CLI (inference.sh, used by web-search)
# Install via official script; we don't know if npm package exists, try a couple paths
echo "[setup] belt (inference.sh CLI)..."
if ! command -v belt >/dev/null 2>&1; then
  npm install -g @inference-sh/cli 2>&1 | tail -3 || \
    echo "  WARN: @inference-sh/cli not found on npm. web-search trace will show failure path."
fi

# cookie-sync npm deps (per its SKILL.md line 26)
if [ -f "$SKILLS_DIR/cookie-sync/package.json" ]; then
  echo "[setup] cookie-sync npm install..."
  (cd "$SKILLS_DIR/cookie-sync" && npm install 2>&1 | tail -3) || echo "  WARN: cookie-sync npm install failed"
fi

# === Tranche-2 toolchains (added 2026-05-09 with 10-skill expansion) ===

# AWS CLI (for cloudformation)
echo "[setup] aws CLI (for cloudformation)..."
if ! command -v aws >/dev/null 2>&1; then
  pip3 install --user --break-system-packages awscli 2>&1 | tail -3 || echo "  WARN: aws CLI install failed"
fi

# Prisma (for prisma-postgres-setup) — installed locally per-project, but also globally for `npx prisma` cache
echo "[setup] prisma..."
npm install -g prisma 2>&1 | tail -3 || echo "  WARN: prisma install failed"

# Semgrep (for semgrep)
echo "[setup] semgrep..."
pip3 install --user --break-system-packages semgrep 2>&1 | tail -3 || echo "  WARN: semgrep install failed"

# Vercel CLI (for vercel-sandbox)
echo "[setup] vercel CLI..."
npm install -g vercel 2>&1 | tail -3 || echo "  WARN: vercel install failed"

# Replicate Python SDK (for prompt-images, used as alternative to raw curl)
echo "[setup] replicate Python SDK..."
pip3 install --user --break-system-packages replicate 2>&1 | tail -3 || echo "  WARN: replicate SDK install failed"

# pinecone-mcp + xcode-project-setup + auth0-quickstart + sentry-setup-ai-monitoring +
# gha-security-review have no CLI install — they rely on inline skill markdown only.
# (xcode-project-setup needs swift, which is not available on Linux — that failure is the data point.)

echo
echo "============================================================"
echo "[setup] complete. installed skills:"
echo "============================================================"
ls "$SKILLS_DIR/"
echo
echo "[setup] per-skill CLIs available:"
for cmd in firecrawl wrangler firebase agent-browser belt; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✓ $cmd"
  else
    echo "  ✗ $cmd (not on PATH — skill may early-fail at exec, captured as data)"
  fi
done
