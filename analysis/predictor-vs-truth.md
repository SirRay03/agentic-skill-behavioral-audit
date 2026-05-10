# Predictor-vs-Truth: F1 per predictor source against same observed traces

Skills compared: 25 production skills (excluding *-aug and zz-*).
Each predictor scored against the same `trace.json` per skill, with the same
v4 agent-infra filter applied to observed paths/hosts.

## Aggregate mean F1 per axis × predictor

| Axis | orig-Claude (n) | fresh-Claude (n) | Codex (n) |
|---|---|---|---|
| paths_read | **0.389** (n=16) | **0.411** (n=16) | **0.451** (n=13) |
| paths_written | **0.393** (n=9) | **0.355** (n=9) | **0.266** (n=7) |
| hosts | **0.431** (n=6) | **0.477** (n=6) | **0.424** (n=5) |

## Per-skill F1 — hosts axis (most stable, key headline)

| Skill | orig | fresh | codex |
|---|---|---|---|
| agent-browser | — | — | — |
| auth0-quickstart | — | — | — |
| azure-validate | — | — | — |
| caveman | — | — | — |
| cloudformation | — | — | — |
| cookie-sync | 0.40 | 0.40 | — |
| find-skills | 0.50 | 0.50 | 0.50 |
| firebase-hosting-basics | 0.36 | 0.55 | 0.18 |
| firebase-security-rules-auditor | — | — | — |
| firecrawl-scrape | — | — | — |
| frontend-design | — | — | — |
| gha-security-review | — | — | — |
| grill-me | — | — | — |
| improve-codebase-architecture | — | — | — |
| pinecone-mcp | — | — | — |
| prisma-postgres-setup | — | — | — |
| prompt-images | — | — | — |
| react-best-practices | — | — | — |
| semgrep | 0.57 | 0.67 | 0.67 |
| sentry-setup-ai-monitoring | — | — | — |
| skill-creator | — | — | — |
| vercel-sandbox | — | — | — |
| web-search | 0.25 | 0.25 | 0.20 |
| wrangler | 0.50 | 0.50 | 0.57 |
| xcode-project-setup | — | — | — |

## Verdict

- **paths_read**: best is **codex** (0.451); spread across predictors = 0.062
- **paths_written**: best is **orig** (0.393); spread across predictors = 0.128
- **hosts**: best is **fresh** (0.477); spread across predictors = 0.053
