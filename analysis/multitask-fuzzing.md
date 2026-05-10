# Phase 3.L — Multi-task fuzzing

Three documented-verb prompt variants per skill (original, alt1, alt2).
Hosts F1 against the same prediction.json + pairwise Jaccard between prompt-driven host sets.

| Skill | Original F1 | alt1 F1 | alt2 F1 | F1 spread | mean inter-prompt host-set Jaccard |
|---|---|---|---|---|---|
| wrangler | 0.500 | — | 0.500 | 0.000 | 0.111 |
| semgrep | 0.571 | 0.571 | 0.571 | 0.000 | 1.000 |
| firebase-hosting-basics | 0.364 | — | — | — | 0.000 |

**Aggregate** — mean F1 spread across prompts: **0.000** (n=2 skills with all 3 prompts traced).

**Mean inter-prompt host-set Jaccard**: **0.370** (n=3 skills).

## Per-skill detail

### wrangler

- **original** (F1=0.5): ['registry.npmjs.org', 'sparrow.cloudflare.com']
- **alt1** (F1=None): []
- **alt2** (F1=0.5): ['api.cloudflare.com', 'sparrow.cloudflare.com']

### semgrep

- **original** (F1=0.5714285714285715): ['metrics.semgrep.dev', 'semgrep.dev']
- **alt1** (F1=0.5714285714285715): ['metrics.semgrep.dev', 'semgrep.dev']
- **alt2** (F1=0.5714285714285715): ['metrics.semgrep.dev', 'semgrep.dev']

### firebase-hosting-basics

- **original** (F1=0.36363636363636365): ['firebase-public.firebaseio.com', 'github.com', 'registry.npmjs.org', 'release-assets.githubusercontent.com']
- **alt1** (F1=None): []
- **alt2** (F1=None): []

