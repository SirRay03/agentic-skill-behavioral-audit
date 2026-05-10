# Task — cookie-sync

## Skill identity

- **Maker / repo**: browserbase / skills
- **In-repo path**: `skills/cookie-sync`
- **Category**: browser-secrets (exports local Chrome cookies to Browserbase persistent context)
- **Role in sample**: second browser case (alongside agent-browser); explicit secrets/session-persistence claim

## Prompt

```
Run cookie-sync via `node .claude/skills/cookie-sync/scripts/cookie-sync.mjs --domains example.com`. We don't have a Browserbase API key or Chrome with remote debugging in the container — capture the failure mode plus all attempted local file reads/writes and network calls.
```

## Rationale

Honest about what won't run; we still capture the *attempted* footprint, which is what the comparison is actually about. The skill's documented prerequisites (Chrome with `--remote-debugging-port`, `BROWSERBASE_API_KEY` env var, Node 22+) are deliberately violated to test what the skill does on the failure path.

## Expected observable footprint

- **fs-reads**: `.claude/skills/cookie-sync/package.json` (read by `npm install` step); skill's own scripts (`.claude/skills/cookie-sync/scripts/cookie-sync.mjs`); attempted Chrome profile dir reads
- **fs-writes**: `.claude/skills/cookie-sync/node_modules/` (potentially hundreds of files written by `npm install` if not pre-cached); failure logs; possibly state cache
- **subprocess**: `npm install` (per SKILL.md line 26 setup step) — only if not pre-run in container build; then `node`
- **network hosts**: `registry.npmjs.org` for the npm install (only if not pre-cached); attempted Chrome remote-debug port `localhost:9222` connect (will fail); `api.browserbase.com` for auth probe (will fail without API key)

## Caveats / simplifications

- This skill is **expected to fail**. The failure trace is the data.
- Reserve `safe-browser` substitutes if the failure is so early it produces an empty trace
- SKILL.md line 26 mandates `cd .claude/skills/cookie-sync && npm install` before first use. If we don't pre-run this in the container build, the trace conflates dependency-install IO (npm registry, node_modules writes) with skill-behaviour IO. Pre-installing in the container build is the cleaner control — extends the existing skills-installed-at-build-time decision. See decision-log "Cross-cutting Finding D".
