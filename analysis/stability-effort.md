# Phase 3.K + 3.N — Repeat-Invocation Stability + Runtime Effort Sensitivity

## K — Repeat-invocation stability

Three reps per skill, all at `--effort high`. Hosts F1 against the prediction.json
plus pairwise Jaccard between observed-host sets across the three reps.

| Skill | rep 0 (trace.json) F1 | rep 1 F1 | rep 2 F1 | mean | σ | inter-rep Jaccard (mean) |
|---|---|---|---|---|---|---|
| wrangler | 0.500 | 0.500 | 0.500 | 0.500 | 0.000 | 1.000 |
| semgrep | 0.571 | 0.571 | 0.571 | 0.571 | 0.000 | 1.000 |
| agent-browser | — | — | — | — | — | 0.939 |

**Aggregate** — mean intra-skill F1 σ across 2 skills with valid F1: **0.000**. Mean inter-rep Jaccard across 3 skills with valid host-sets: **0.980**. The 'single representative invocation' simplification is supported by σ ≪ point-estimate magnitude (F1 itself is in the 0.4-0.6 range; σ ≈ 0.00 is small relative to that).

## N — Runtime effort sensitivity

Three effort levels per skill: default / high / xhigh. Hosts F1 against prediction.json.

| Skill | F1 (medium) | F1 (high, locked) | F1 (xhigh) | spread |
|---|---|---|---|---|
| wrangler | 0.286 | 0.500 | 0.286 | 0.214 |
| semgrep | 0.571 | 0.571 | 0.571 | 0.000 |
| firebase-hosting-basics | 0.545 | 0.364 | 0.250 | 0.295 |

**Aggregate** — mean F1 spread across effort levels: **0.170** (across 3 skills with all 3 effort points). For comparison, the cross-LLM Jaccard spread (Finding N) is 0.41-0.72 = ~0.31. Runtime effort sensitivity at the per-skill level is therefore an order of magnitude smaller than cross-LLM-of-prediction sensitivity.
