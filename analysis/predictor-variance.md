# Predictor Variance: original-Claude vs fresh-Claude vs Codex

Skills with all three prediction sources: 26 / 26

## Aggregate mean Jaccard similarity

Higher Jaccard = more agreement on which items are predicted. Empty-vs-empty pairs
are excluded from the mean (jaccard undefined).

**Note on n discrepancy vs `analysis/stats.md`**: this file computes Jaccard over all
26 rows (25 production skills + 1 adversarial demo), giving n=24 / n=19–20 depending
on axis. `stats.md` computes bootstrapped CIs excluding the adversarial demo (n-1 on
non-empty-pair count), yielding values that differ by ~0.02–0.03. `stats.md` is the
canonical source for report headline numbers; these raw values are for exploratory
reference only.

| axis | orig vs fresh | orig vs codex | fresh vs codex | n (this file) |
|---|---|---|---|---|
| paths_read | 0.599 | 0.202 | 0.244 | 24 |
| paths_written | 0.574 | 0.171 | 0.189 | 19 |
| hosts | 0.737 | 0.459 | 0.440 | 20 |
| subprocesses | 0.811 | 0.594 | 0.554 | 20 |

## Per-skill detail (hosts axis only, for brevity)

| skill | n_orig | n_fresh | n_codex | jacc(o,f) | jacc(o,c) | jacc(f,c) |
|---|---|---|---|---|---|---|
| agent-browser | 1 | 6 | 10 | 0.00 | 0.10 | 0.14 |
| auth0-quickstart | 5 | 5 | 6 | 1.00 | 0.83 | 0.83 |
| azure-validate | 4 | 3 | 11 | 0.75 | 0.15 | 0.17 |
| caveman | 0 | 0 | 0 | — | — | — |
| cloudformation | 3 | 3 | 2 | 1.00 | 0.67 | 0.67 |
| cookie-sync | 4 | 4 | 11 | 1.00 | 0.25 | 0.25 |
| find-skills | 5 | 5 | 5 | 1.00 | 0.67 | 0.67 |
| firebase-hosting-basics | 7 | 7 | 7 | 0.08 | 0.40 | 0.08 |
| firebase-security-rules-auditor | 0 | 0 | 0 | — | — | — |
| firecrawl-scrape | 2 | 2 | 3 | 1.00 | 0.25 | 0.25 |
| frontend-design | 5 | 5 | 3 | 0.67 | 0.60 | 0.33 |
| gha-security-review | 0 | 0 | 0 | — | — | — |
| grill-me | 0 | 0 | 0 | — | — | — |
| improve-codebase-architecture | 0 | 0 | 0 | — | — | — |
| pinecone-mcp | 2 | 1 | 3 | 0.50 | 0.67 | 0.33 |
| prisma-postgres-setup | 3 | 3 | 4 | 1.00 | 0.75 | 0.75 |
| prompt-images | 0 | 2 | 3 | 0.00 | 0.00 | 0.67 |
| react-best-practices | 0 | 0 | 0 | — | — | — |
| semgrep | 5 | 4 | 3 | 0.80 | 0.60 | 0.40 |
| sentry-setup-ai-monitoring | 4 | 5 | 7 | 0.80 | 0.10 | 0.09 |
| skill-creator | 1 | 1 | 2 | 1.00 | 0.50 | 0.50 |
| vercel-sandbox | 5 | 6 | 7 | 0.57 | 0.20 | 0.18 |
| web-search | 5 | 5 | 7 | 1.00 | 0.71 | 0.71 |
| wrangler | 6 | 6 | 5 | 1.00 | 0.57 | 0.57 |
| xcode-project-setup | 6 | 5 | 1 | 0.57 | 0.17 | 0.20 |
| zz-adversarial-summarize-text | 1 | 1 | 1 | 1.00 | 1.00 | 1.00 |
