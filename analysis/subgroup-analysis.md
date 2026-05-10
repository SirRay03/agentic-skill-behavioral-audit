# Phase 3.M — Subgroup Analysis

n production skills with F1 data: 25 (excluding *-aug and zz-*)

## Stratifications tested

1. **Maker organisation**: Anthropic / Cloudflare / Firebase / Microsoft / Vercel Labs / vendor-other / solo-dev
2. **Maker bucket** (binary): established-vendor (top-5 makers) vs long-tail
3. **Skill category**: deploy / knowledge / network / browser / audit / fs-edit / meta / mcp / multi-modal / etc.
4. **SKILL.md length quartile**: Q1 (≤Q1 lines) vs Q2-Q3 vs Q4 (≥Q3 lines)
5. **Bimodal split** (binary): CLI-wrapper vs pure-text/single-output

## Tests applied

- For 3+ groups: Kruskal-Wallis H test (non-parametric, robust to small n + non-normal distributions).
- For binary splits: Mann-Whitney U test.
- All p-values are two-sided.

## 1. Established vendor vs long-tail (binary split)

- **established-vendor vs long-tail** (f1_paths_read): U = 28.0, p = 0.7209, n = (8, 8)
- **established-vendor vs long-tail** (f1_paths_written): U = 6.0, p = 0.8889, n = (7, 2)
- **established-vendor vs long-tail** (f1_hosts): U = 5.0, p = 1.0000, n = (3, 3)

## 2. By skill category (multi-group)

- **by category** (f1_paths_read): Kruskal-Wallis H = 14.294, p = 0.2171, n_groups = 12, n_total = 16
- **by category** (f1_paths_written): Kruskal-Wallis H = 7.378, p = 0.2873, n_groups = 7, n_total = 9
- **by category** (f1_hosts): Kruskal-Wallis H = 4.081, p = 0.3952, n_groups = 5, n_total = 6

## 3. By SKILL.md length quartile (Q1 / Q2-Q3 / Q4)

- **by SKILL.md length quartile** (f1_paths_read): Kruskal-Wallis H = 1.783, p = 0.4100, n_groups = 3, n_total = 16
- **by SKILL.md length quartile** (f1_paths_written): Kruskal-Wallis H = 0.344, p = 0.8418, n_groups = 3, n_total = 9
- **by SKILL.md length quartile** (f1_hosts): Kruskal-Wallis H = 2.855, p = 0.2399, n_groups = 3, n_total = 6

## 4. CLI-wrapper vs pure-text/single-output (bimodal split)

- **CLI-wrapper vs pure-text** (f1_paths_read): U = 6.0, p = 0.0297, n = (12, 4)
- **CLI-wrapper vs pure-text** (f1_paths_written): U = 7.0, p = 0.4444, n = (8, 1)
_CLI-wrapper vs pure-text_: insufficient data

## Verdict

**Bimodal split is statistically significant at α=0.05 on**: f1_paths_read.

This converts the report's 'bimodal F1 distribution' claim from descriptive to formally tested. The CLI-wrapper cluster has a *significantly different* F1 distribution from the pure-text/single-output cluster, with the CLI-wrappers concentrated at the low end (Findings C, G) and pure-text skills at the high end.
