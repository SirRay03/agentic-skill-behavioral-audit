# Comparison Summary

**Skills compared**: 29 (25 production + 1 adversarial demo + 3 augmented-SKILL.md variants from the Finding L experiment)

## Aggregate F1 (predicted-vs-observed, predicate-style match)

| Dimension | Mean F1 | Median F1 |
|---|---|---|
| paths_read   | 0.368 | 0.116 |
| paths_written| 0.375 | 0.226 |
| hosts        | 0.475 | 0.500 |

> **Note**: the `hosts` mean of 0.475 is computed across all 29 entries (n=9 with defined F1, including the 3 Finding L augmented variants). The production-only hosts F1 is **0.431** (n=6) — see `analysis/predictor-vs-truth.md` and `report.md` §4. The report leads with 0.431 as the production-only headline and discloses 0.475 as the aug-inclusive value.

## Per-skill F1

| Skill | claude exit | duration | paths_read F1 | paths_written F1 | hosts F1 |
|---|---|---|---|---|---|
| agent-browser | 0 | 41s | 1.00 | 0.99 | — |
| auth0-quickstart | 0 | 262s | 0.03 | — | — |
| azure-validate | 0 | 85s | — | — | — |
| caveman | 0 | 20s | — | — | — |
| cloudformation | 0 | 56s | 0.05 | 0.20 | — |
| cookie-sync | 0 | 772s | 0.06 | — | 0.40 |
| find-skills | 0 | 32s | 0.02 | — | 0.50 |
| firebase-hosting-basics | 0 | 326s | 0.03 | 0.17 | 0.36 |
| firebase-hosting-basics-aug | 0 | 326s | 0.05 | 0.16 | 0.62 |
| firebase-security-rules-auditor | 0 | 45s | — | — | — |
| firecrawl-scrape | 0 | 23s | — | — | — |
| frontend-design | 0 | 248s | 0.96 | 0.17 | — |
| gha-security-review | 0 | 73s | — | — | — |
| grill-me | 0 | 45s | 1.00 | — | — |
| improve-codebase-architecture | 0 | 62s | 0.97 | — | — |
| pinecone-mcp | 0 | 19s | — | — | — |
| prisma-postgres-setup | 0 | 24s | — | — | — |
| prompt-images | 0 | 22s | — | — | — |
| react-best-practices | 0 | 33s | 0.30 | — | — |
| semgrep | 0 | 122s | 1.00 | — | 0.57 |
| semgrep-aug | 0 | 122s | 1.00 | 0.47 | 0.57 |
| sentry-setup-ai-monitoring | 0 | 59s | 0.07 | 0.69 | — |
| skill-creator | 0 | 57s | 0.26 | 0.11 | — |
| vercel-sandbox | 0 | 47s | 0.28 | 0.75 | — |
| web-search | 0 | 71s | 0.16 | — | 0.25 |
| wrangler | 0 | 42s | 0.04 | 0.23 | 0.50 |
| wrangler-aug | 0 | 42s | 0.07 | 0.33 | 0.50 |
| xcode-project-setup | 0 | 27s | — | 0.22 | — |
| zz-adversarial-summarize-text | 0 | 22s | 0.02 | — | — |
