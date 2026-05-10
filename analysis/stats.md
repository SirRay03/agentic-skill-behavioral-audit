# Phase 1.B — Statistical Rigor Pass

## 1. Bootstrap 95% CIs on aggregate F1 (n=25 + adversarial + 3 augmented)

Resampled 1000 times with seed 20260509. CI excludes empty-vs-empty pairs (F1 undefined).

| Axis | n with defined F1 | mean | 95% CI |
|---|---|---|---|
| paths_read | 20 | 0.368 | [0.185, 0.548] |
| paths_written | 12 | 0.375 | [0.235, 0.543] |
| hosts | 9 | 0.475 | [0.399, 0.542] |

## 2. Bootstrap 95% CIs on predictor-variance Jaccard (n=25, fresh-batch)

| Axis | comparison | n | mean | 95% CI |
|---|---|---|---|---|
| paths_read | orig vs fresh | 22 | 0.580 | [0.451, 0.703] |
| paths_read | orig vs codex | 23 | 0.210 | [0.120, 0.302] |
| paths_read | fresh vs codex | 23 | 0.255 | [0.149, 0.359] |
| paths_written | orig vs fresh | 19 | 0.574 | [0.414, 0.722] |
| paths_written | orig vs codex | 19 | 0.171 | [0.093, 0.261] |
| paths_written | fresh vs codex | 19 | 0.189 | [0.106, 0.279] |
| hosts | orig vs fresh | 19 | 0.723 | [0.550, 0.868] |
| hosts | orig vs codex | 19 | 0.431 | [0.304, 0.548] |
| hosts | fresh vs codex | 19 | 0.410 | [0.295, 0.522] |
| subprocesses | orig vs fresh | 18 | 0.801 | [0.705, 0.888] |
| subprocesses | orig vs codex | 19 | 0.572 | [0.428, 0.719] |
| subprocesses | fresh vs codex | 19 | 0.531 | [0.401, 0.667] |

## 3. Paired tests: static-regex recall vs LLM xhigh recall

### McNemar's test (host-level pairing across all observed hosts)

- Both predictors caught the host (a): 6
- Only static caught (b): 1
- Only LLM caught (c): 12
- Neither caught (d): 15
- Two-sided exact-binomial p-value: **0.003418**
- Verdict: reject H0 (static and LLM disagree on which hosts they catch). LLM caught 12 hosts static missed; static caught 1 hosts LLM missed.

### Wilcoxon signed-rank on per-skill recall pairs

- n pairs: 11
- static recall mean: 0.273
- LLM recall mean:    0.682
- Mean difference (LLM - static): +0.409
- Two-sided p-value: **0.04688**

## 4. Bimodal cluster size CIs (paths_read F1 distribution)

- **high cluster (F1 ≥ 0.95)**: 6/20 = 0.300, 95% Wilson CI [0.145, 0.519]
- **low cluster (F1 < 0.10)**: 10/20 = 0.500, 95% Wilson CI [0.299, 0.701]

Skills in the high cluster: agent-browser, frontend-design, grill-me, improve-codebase-architecture, semgrep, semgrep-aug

Skills in the low cluster: auth0-quickstart, cloudformation, cookie-sync, find-skills, firebase-hosting-basics, firebase-hosting-basics-aug, sentry-setup-ai-monitoring, wrangler, wrangler-aug, zz-adversarial-summarize-text

## 5. Headline 'LLM is 2.5× better than static regex' — re-derived

- Static recall mean: 0.273, 95% CI [0.061, 0.515]
- LLM recall mean:    0.682, 95% CI [0.424, 0.909]
- Ratio (LLM / static): **2.50×**

Paired Wilcoxon p = 0.04688; the 2.5× claim is statistically significant at α=0.05.
