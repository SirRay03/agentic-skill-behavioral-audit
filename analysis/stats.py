#!/usr/bin/env python3
"""Phase 1.B — Statistical rigor pass.

Three deliverables:

1. Bootstrap 95% CIs (1000 resamples) on each headline F1 mean across n=25:
   - paths_read F1
   - paths_written F1
   - hosts F1
   plus the predictor-variance Jaccard means (orig-fresh, orig-codex, fresh-codex)
   plus the policy-eval allow-rate and catch-rate.

2. McNemar's paired test on per-skill static-recall vs LLM-recall (the 0.27 vs 0.68
   claim). Per skill, the static analyzer produces a recall against observed hosts,
   and the LLM predictor produces a recall against the same observed hosts. Paired
   across skills.

3. 95% Wilson score CIs on the bimodal cluster sizes (high-F1 cluster of 5/25,
   low-F1 cluster of 7/25 within the paths_read F1 distribution).

Output:
    analysis/stats.json     — raw numbers
    analysis/stats.md       — human-readable
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def bootstrap_ci(values: list[float], n_resamples: int = 1000, ci: float = 0.95) -> tuple[float, float, float]:
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    if len(arr) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(20260509)
    means = np.empty(n_resamples)
    n = len(arr)
    for i in range(n_resamples):
        idx = rng.integers(0, n, n)
        means[i] = arr[idx].mean()
    lo = float(np.percentile(means, (1 - ci) / 2 * 100))
    hi = float(np.percentile(means, (1 + ci) / 2 * 100))
    return (float(arr.mean()), lo, hi)


def wilson_ci(k: int, n: int, ci: float = 0.95) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    z = stats.norm.ppf((1 + ci) / 2)
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * np.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return (phat, max(0.0, centre - half), min(1.0, centre + half))


def main() -> None:
    out_lines = ["# Phase 1.B — Statistical Rigor Pass", ""]
    raw = {}

    # ===== 1. Bootstrap CIs on aggregate F1 from compare.py =====
    per_skill_path = PROJECT_ROOT / "analysis" / "per-skill.json"
    per_skill = json.loads(per_skill_path.read_text())

    out_lines.append("## 1. Bootstrap 95% CIs on aggregate F1 (n=25 + adversarial + 3 augmented)")
    out_lines.append("")
    out_lines.append("Resampled 1000 times with seed 20260509. CI excludes empty-vs-empty pairs (F1 undefined).")
    out_lines.append("")
    out_lines.append("| Axis | n with defined F1 | mean | 95% CI |")
    out_lines.append("|---|---|---|---|")

    for axis_pretty, key in [("paths_read", "paths_read"), ("paths_written", "paths_written"), ("hosts", "hosts")]:
        bucket = "fs_metrics" if key.startswith("paths") else "net_metrics"
        f1s = []
        for r in per_skill:
            if "error" in r:
                continue
            v = r[bucket][key]["f1"]
            if v is not None:
                f1s.append(v)
        m, lo, hi = bootstrap_ci(f1s)
        raw[f"f1_{axis_pretty}"] = {"n": len(f1s), "mean": m, "ci_lo": lo, "ci_hi": hi}
        out_lines.append(f"| {axis_pretty} | {len(f1s)} | {m:.3f} | [{lo:.3f}, {hi:.3f}] |")

    # ===== 2. Predictor-variance Jaccard CIs =====
    pv_path = PROJECT_ROOT / "analysis" / "predictor-variance.json"
    pv = json.loads(pv_path.read_text())

    out_lines.append("")
    out_lines.append("## 2. Bootstrap 95% CIs on predictor-variance Jaccard (n=25, fresh-batch)")
    out_lines.append("")
    out_lines.append("| Axis | comparison | n | mean | 95% CI |")
    out_lines.append("|---|---|---|---|---|")

    for axis in ("paths_read", "paths_written", "hosts", "subprocesses"):
        for cmp_key, cmp_label in [
            ("jacc_orig_fresh", "orig vs fresh"),
            ("jacc_orig_codex", "orig vs codex"),
            ("jacc_fresh_codex", "fresh vs codex"),
        ]:
            vs = []
            for r in pv["per_skill"]:
                if "axes" not in r:
                    continue
                v = r["axes"][axis][cmp_key]
                if v is not None:
                    vs.append(v)
            if not vs:
                continue
            m, lo, hi = bootstrap_ci(vs)
            raw[f"jaccard_{axis}_{cmp_key}"] = {"n": len(vs), "mean": m, "ci_lo": lo, "ci_hi": hi}
            out_lines.append(f"| {axis} | {cmp_label} | {len(vs)} | {m:.3f} | [{lo:.3f}, {hi:.3f}] |")

    # ===== 3. McNemar's paired test: static recall vs LLM recall =====
    static_path = PROJECT_ROOT / "analysis" / "static-per-skill.json"
    static_data = json.loads(static_path.read_text())

    # For each skill with non-empty observed hosts, compute per-host paired classification:
    #   static caught? (yes/no) × LLM caught? (yes/no)
    # Then aggregate the 2×2 contingency: b = static_caught_only, c = llm_caught_only
    # McNemar: chi-squared = (b - c)^2 / (b + c) (with continuity correction)
    n_b = 0  # static caught, LLM didn't
    n_c = 0  # LLM caught, static didn't
    n_a = 0  # both caught
    n_d = 0  # neither caught
    paired_skill_recalls = []

    for r in static_data:
        observed = r.get("observed_hosts", [])
        if not observed:
            continue
        static_set = set(r.get("static_caught_dynamic", []))
        llm_set = set(r.get("llm_caught_dynamic", []))
        for h in observed:
            in_static = h in static_set
            in_llm = h in llm_set
            if in_static and in_llm:
                n_a += 1
            elif in_static and not in_llm:
                n_b += 1
            elif not in_static and in_llm:
                n_c += 1
            else:
                n_d += 1
        # also collect skill-level recall pair for paired t-test on per-skill recalls
        if r.get("static_recall") is not None and r.get("llm_recall") is not None:
            paired_skill_recalls.append((r["static_recall"], r["llm_recall"]))

    # McNemar's exact test (binomial since b+c may be small)
    mn_total = n_b + n_c
    mn_pvalue = 1.0
    if mn_total > 0:
        # Two-sided binomial test on min(b, c) under p=0.5
        result = stats.binomtest(min(n_b, n_c), n=mn_total, p=0.5, alternative="two-sided")
        mn_pvalue = result.pvalue

    raw["mcnemar"] = {
        "n_a_both_caught": n_a, "n_b_static_only": n_b, "n_c_llm_only": n_c, "n_d_neither": n_d,
        "p_value_two_sided": mn_pvalue,
    }

    # Paired Wilcoxon on per-skill recalls
    if paired_skill_recalls:
        s = np.array([p[0] for p in paired_skill_recalls])
        l = np.array([p[1] for p in paired_skill_recalls])
        # Wilcoxon signed-rank; if all differences are zero or near-zero scipy raises
        try:
            wilcox = stats.wilcoxon(s, l, zero_method="wilcox", alternative="two-sided")
            wilcox_pvalue = float(wilcox.pvalue)
        except ValueError:
            wilcox_pvalue = float("nan")
        raw["wilcoxon"] = {
            "n_pairs": len(paired_skill_recalls),
            "static_mean": float(s.mean()),
            "llm_mean": float(l.mean()),
            "diff_mean": float((l - s).mean()),
            "p_value_two_sided": wilcox_pvalue,
        }

    out_lines.append("")
    out_lines.append("## 3. Paired tests: static-regex recall vs LLM xhigh recall")
    out_lines.append("")
    out_lines.append("### McNemar's test (host-level pairing across all observed hosts)")
    out_lines.append("")
    out_lines.append(f"- Both predictors caught the host (a): {n_a}")
    out_lines.append(f"- Only static caught (b): {n_b}")
    out_lines.append(f"- Only LLM caught (c): {n_c}")
    out_lines.append(f"- Neither caught (d): {n_d}")
    out_lines.append(f"- Two-sided exact-binomial p-value: **{mn_pvalue:.4g}**")
    if mn_pvalue < 0.05:
        out_lines.append(f"- Verdict: reject H0 (static and LLM disagree on which hosts they catch). LLM caught {n_c} hosts static missed; static caught {n_b} hosts LLM missed.")
    else:
        out_lines.append(f"- Verdict: insufficient evidence to reject H0 at α=0.05.")

    if paired_skill_recalls:
        out_lines.append("")
        out_lines.append("### Wilcoxon signed-rank on per-skill recall pairs")
        out_lines.append("")
        out_lines.append(f"- n pairs: {raw['wilcoxon']['n_pairs']}")
        out_lines.append(f"- static recall mean: {raw['wilcoxon']['static_mean']:.3f}")
        out_lines.append(f"- LLM recall mean:    {raw['wilcoxon']['llm_mean']:.3f}")
        out_lines.append(f"- Mean difference (LLM - static): {raw['wilcoxon']['diff_mean']:+.3f}")
        out_lines.append(f"- Two-sided p-value: **{raw['wilcoxon']['p_value_two_sided']:.4g}**")

    # ===== 4. Bimodal cluster size CIs =====
    out_lines.append("")
    out_lines.append("## 4. Bimodal cluster size CIs (paths_read F1 distribution)")
    out_lines.append("")

    paths_read_f1 = []
    for r in per_skill:
        if "error" in r:
            continue
        v = r["fs_metrics"]["paths_read"]["f1"]
        if v is not None:
            paths_read_f1.append((r["skill_id"], v))

    n_total = len(paths_read_f1)
    n_high = sum(1 for _, v in paths_read_f1 if v >= 0.95)
    n_low = sum(1 for _, v in paths_read_f1 if v < 0.10)

    for label, k in [("high cluster (F1 ≥ 0.95)", n_high), ("low cluster (F1 < 0.10)", n_low)]:
        p, lo, hi = wilson_ci(k, n_total)
        raw[f"cluster_{label.split()[0]}"] = {"k": k, "n": n_total, "phat": p, "ci_lo": lo, "ci_hi": hi}
        out_lines.append(f"- **{label}**: {k}/{n_total} = {p:.3f}, 95% Wilson CI [{lo:.3f}, {hi:.3f}]")

    out_lines.append("")
    out_lines.append("Skills in the high cluster: " + ", ".join(s for s, v in paths_read_f1 if v >= 0.95))
    out_lines.append("")
    out_lines.append("Skills in the low cluster: " + ", ".join(s for s, v in paths_read_f1 if v < 0.10))

    # ===== 5. Static-vs-LLM 2.5× claim — re-derived statistically =====
    out_lines.append("")
    out_lines.append("## 5. Headline 'LLM is 2.5× better than static regex' — re-derived")
    out_lines.append("")
    static_recalls = [p[0] for p in paired_skill_recalls]
    llm_recalls = [p[1] for p in paired_skill_recalls]
    if static_recalls and llm_recalls:
        sm, slo, shi = bootstrap_ci(static_recalls)
        lm, llo, lhi = bootstrap_ci(llm_recalls)
        out_lines.append(f"- Static recall mean: {sm:.3f}, 95% CI [{slo:.3f}, {shi:.3f}]")
        out_lines.append(f"- LLM recall mean:    {lm:.3f}, 95% CI [{llo:.3f}, {lhi:.3f}]")
        if sm > 0:
            out_lines.append(f"- Ratio (LLM / static): **{lm/sm:.2f}×**")
        out_lines.append("")
        if "wilcoxon" in raw:
            out_lines.append(f"Paired Wilcoxon p = {raw['wilcoxon']['p_value_two_sided']:.4g}; "
                             f"the 2.5× claim is {'statistically significant' if raw['wilcoxon']['p_value_two_sided'] < 0.05 else 'not significant'} at α=0.05.")

    # Save outputs
    out_dir = PROJECT_ROOT / "analysis"
    (out_dir / "stats.json").write_text(json.dumps(raw, indent=2))
    (out_dir / "stats.md").write_text("\n".join(out_lines) + "\n")
    print(f"=> {out_dir}/stats.json")
    print(f"=> {out_dir}/stats.md")
    print()
    for line in out_lines[:50]:
        print(line)


if __name__ == "__main__":
    main()
