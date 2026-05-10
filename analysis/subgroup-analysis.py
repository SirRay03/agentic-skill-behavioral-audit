#!/usr/bin/env python3
"""Phase 3.M — Subgroup analysis + ANOVA / Mann-Whitney.

Slice the n=25 production-skill F1 distribution by three stratifications:
  - Maker organization (Anthropic / Cloudflare / Firebase / Vercel Labs / vendor-other / solo-dev)
  - Skill category (deploy / network / browser / audit / fs-edit / knowledge / meta / etc.)
  - SKILL.md length quartile (Q1 short / Q4 long)

For each stratification, run a non-parametric Kruskal-Wallis test (3+ groups,
robust to non-normality on small n). For the binary-split bimodal-cluster claim,
run Mann-Whitney U (CLI-wrappers vs pure-text/single-output skills).

Outputs analysis/subgroup-analysis.{json,md}.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Per-skill metadata for stratification (n=25 production skills only)
SKILL_META = {
    # tranche 1
    "frontend-design":               {"maker": "Anthropic",   "category": "knowledge"},
    "skill-creator":                 {"maker": "Anthropic",   "category": "fs-write-meta"},
    "react-best-practices":          {"maker": "Vercel Labs", "category": "knowledge"},
    "web-search":                    {"maker": "vendor-other","category": "network"},
    "firecrawl-scrape":              {"maker": "vendor-other","category": "network-broad"},
    "agent-browser":                 {"maker": "Vercel Labs", "category": "browser"},
    "firebase-hosting-basics":       {"maker": "Firebase",    "category": "deploy"},
    "wrangler":                      {"maker": "Cloudflare",  "category": "deploy"},
    "azure-validate":                {"maker": "Microsoft",   "category": "deploy"},
    "find-skills":                   {"maker": "Vercel Labs", "category": "meta"},
    "grill-me":                      {"maker": "solo-dev",    "category": "knowledge"},
    "improve-codebase-architecture": {"maker": "solo-dev",    "category": "fs-edit"},
    "firebase-security-rules-auditor":{"maker":"Firebase",    "category": "audit"},
    "cookie-sync":                   {"maker": "vendor-other","category": "browser-secrets"},
    "caveman":                       {"maker": "solo-dev",    "category": "knowledge"},
    # tranche 2
    "cloudformation":                {"maker": "solo-dev",    "category": "deploy"},
    "pinecone-mcp":                  {"maker": "vendor-other","category": "meta-mcp"},
    "prompt-images":                 {"maker": "vendor-other","category": "multi-modal"},
    "prisma-postgres-setup":         {"maker": "vendor-other","category": "db-setup"},
    "auth0-quickstart":              {"maker": "vendor-other","category": "auth-identity"},
    "sentry-setup-ai-monitoring":    {"maker": "vendor-other","category": "observability"},
    "gha-security-review":           {"maker": "vendor-other","category": "audit"},
    "semgrep":                       {"maker": "vendor-other","category": "security-scan"},
    "vercel-sandbox":                {"maker": "Vercel Labs", "category": "vercel-specific"},
    "xcode-project-setup":           {"maker": "Firebase",    "category": "mobile-native"},
}

# Group "vendor-other" + "solo-dev" together as "long tail" for some splits
def maker_bucket(m: str) -> str:
    if m in ("Anthropic", "Cloudflare", "Firebase", "Vercel Labs", "Microsoft"):
        return "established-vendor"
    return "long-tail"

# Bimodal split: which skills are "CLI-wrapper" vs "pure-text/single-output"
# Used for the formal bimodal-cluster Mann-Whitney test
CLI_WRAPPER = {
    "wrangler", "firebase-hosting-basics", "azure-validate", "cloudformation",
    "auth0-quickstart", "prisma-postgres-setup", "sentry-setup-ai-monitoring",
    "vercel-sandbox", "find-skills", "cookie-sync", "web-search",
    "firecrawl-scrape", "prompt-images", "agent-browser", "semgrep",
    "xcode-project-setup", "skill-creator", "pinecone-mcp",
}
PURE_TEXT = {
    "frontend-design", "react-best-practices", "grill-me", "caveman",
    "improve-codebase-architecture", "firebase-security-rules-auditor",
    "gha-security-review",
}


def main():
    per_skill = json.loads((PROJECT_ROOT / "analysis" / "per-skill.json").read_text())

    # Filter to production skills only (skip *-aug and zz-*)
    rows = []
    for r in per_skill:
        if "error" in r:
            continue
        sid = r["skill_id"]
        if sid.endswith("-aug") or sid.startswith("zz-"):
            continue
        if sid not in SKILL_META:
            continue
        meta = SKILL_META[sid]
        skill_md_path = PROJECT_ROOT / "skills" / sid / "SKILL.md"
        n_lines = len(skill_md_path.read_text().splitlines()) if skill_md_path.exists() else None
        rows.append({
            "skill_id": sid,
            "maker": meta["maker"],
            "maker_bucket": maker_bucket(meta["maker"]),
            "category": meta["category"],
            "skill_md_lines": n_lines,
            "f1_paths_read": r["fs_metrics"]["paths_read"]["f1"],
            "f1_paths_written": r["fs_metrics"]["paths_written"]["f1"],
            "f1_hosts": r["net_metrics"]["hosts"]["f1"],
        })

    # SKILL.md length quartiles (only for skills with non-None paths_read F1)
    valid_for_quartile = [r for r in rows if r["skill_md_lines"] is not None]
    if valid_for_quartile:
        lengths = sorted(r["skill_md_lines"] for r in valid_for_quartile)
        q1, q3 = np.percentile(lengths, [25, 75])
        for r in rows:
            if r["skill_md_lines"] is None:
                r["length_bucket"] = None
            elif r["skill_md_lines"] <= q1:
                r["length_bucket"] = f"Q1 (<={q1:.0f} lines)"
            elif r["skill_md_lines"] >= q3:
                r["length_bucket"] = f"Q4 (>={q3:.0f} lines)"
            else:
                r["length_bucket"] = "Q2-Q3"

    # ANOVA / Kruskal-Wallis on each stratification × axis combination
    out = {"per_skill": rows, "tests": {}}
    lines = [
        "# Phase 3.M — Subgroup Analysis",
        "",
        f"n production skills with F1 data: {len(rows)} (excluding *-aug and zz-*)",
        "",
        "## Stratifications tested",
        "",
        "1. **Maker organisation**: Anthropic / Cloudflare / Firebase / Microsoft / Vercel Labs / vendor-other / solo-dev",
        "2. **Maker bucket** (binary): established-vendor (top-5 makers) vs long-tail",
        "3. **Skill category**: deploy / knowledge / network / browser / audit / fs-edit / meta / mcp / multi-modal / etc.",
        "4. **SKILL.md length quartile**: Q1 (≤Q1 lines) vs Q2-Q3 vs Q4 (≥Q3 lines)",
        "5. **Bimodal split** (binary): CLI-wrapper vs pure-text/single-output",
        "",
        "## Tests applied",
        "",
        "- For 3+ groups: Kruskal-Wallis H test (non-parametric, robust to small n + non-normal distributions).",
        "- For binary splits: Mann-Whitney U test.",
        "- All p-values are two-sided.",
        "",
    ]

    def values_by(rows, group_key, f1_key):
        groups = {}
        for r in rows:
            g = r.get(group_key)
            v = r.get(f1_key)
            if g is None or v is None:
                continue
            groups.setdefault(g, []).append(v)
        return groups

    def report_kruskal(label, groups_dict, axis):
        groups = [v for v in groups_dict.values() if len(v) >= 1]
        n_groups = len(groups)
        if n_groups < 2:
            return f"_{label}_: only {n_groups} group with data, test not applicable", None, None
        try:
            stat, p = stats.kruskal(*groups)
        except ValueError:
            return f"_{label}_: kruskal failed (degenerate group sizes)", None, None
        n_total = sum(len(g) for g in groups)
        return (f"- **{label}** ({axis}): Kruskal-Wallis H = {stat:.3f}, p = {p:.4f}, "
                f"n_groups = {n_groups}, n_total = {n_total}"), float(stat), float(p)

    def report_mwu(label, group_a, group_b, axis):
        if len(group_a) < 1 or len(group_b) < 1:
            return f"_{label}_: insufficient data", None, None
        try:
            stat, p = stats.mannwhitneyu(group_a, group_b, alternative="two-sided")
        except ValueError:
            return f"_{label}_: mwu failed", None, None
        return (f"- **{label}** ({axis}): U = {stat:.1f}, p = {p:.4f}, "
                f"n = ({len(group_a)}, {len(group_b)})"), float(stat), float(p)

    # ============================================================
    # Stratification 1 — by maker bucket (binary), all three axes
    # ============================================================
    lines.append("## 1. Established vendor vs long-tail (binary split)")
    lines.append("")
    out["tests"]["maker_bucket"] = {}
    for axis in ("f1_paths_read", "f1_paths_written", "f1_hosts"):
        groups = values_by(rows, "maker_bucket", axis)
        a = groups.get("established-vendor", [])
        b = groups.get("long-tail", [])
        line, U, p = report_mwu("established-vendor vs long-tail", a, b, axis)
        lines.append(line)
        out["tests"]["maker_bucket"][axis] = {"U": U, "p": p,
                                              "n_established_vendor": len(a),
                                              "n_long_tail": len(b),
                                              "median_established": float(np.median(a)) if a else None,
                                              "median_long_tail":  float(np.median(b)) if b else None}
    lines.append("")

    # ============================================================
    # Stratification 2 — by skill category (multi-group)
    # ============================================================
    lines.append("## 2. By skill category (multi-group)")
    lines.append("")
    out["tests"]["category"] = {}
    for axis in ("f1_paths_read", "f1_paths_written", "f1_hosts"):
        groups = values_by(rows, "category", axis)
        line, H, p = report_kruskal("by category", groups, axis)
        lines.append(line)
        out["tests"]["category"][axis] = {"H": H, "p": p,
                                          "groups": {g: {"n": len(v), "median": float(np.median(v)) if v else None}
                                                     for g, v in groups.items()}}
    lines.append("")

    # ============================================================
    # Stratification 3 — by SKILL.md length quartile (3 groups)
    # ============================================================
    lines.append("## 3. By SKILL.md length quartile (Q1 / Q2-Q3 / Q4)")
    lines.append("")
    out["tests"]["length_bucket"] = {}
    for axis in ("f1_paths_read", "f1_paths_written", "f1_hosts"):
        groups = values_by(rows, "length_bucket", axis)
        line, H, p = report_kruskal("by SKILL.md length quartile", groups, axis)
        lines.append(line)
        out["tests"]["length_bucket"][axis] = {"H": H, "p": p,
                                               "groups": {g: {"n": len(v), "median": float(np.median(v)) if v else None}
                                                          for g, v in groups.items()}}
    lines.append("")

    # ============================================================
    # Stratification 4 — bimodal split (CLI-wrapper vs pure-text)
    # ============================================================
    lines.append("## 4. CLI-wrapper vs pure-text/single-output (bimodal split)")
    lines.append("")
    out["tests"]["bimodal"] = {}
    for axis in ("f1_paths_read", "f1_paths_written", "f1_hosts"):
        cli_vals = [r[axis] for r in rows if r["skill_id"] in CLI_WRAPPER and r[axis] is not None]
        pure_vals = [r[axis] for r in rows if r["skill_id"] in PURE_TEXT and r[axis] is not None]
        line, U, p = report_mwu("CLI-wrapper vs pure-text", cli_vals, pure_vals, axis)
        lines.append(line)
        out["tests"]["bimodal"][axis] = {
            "U": U, "p": p,
            "n_cli_wrapper": len(cli_vals), "n_pure_text": len(pure_vals),
            "median_cli_wrapper": float(np.median(cli_vals)) if cli_vals else None,
            "median_pure_text":  float(np.median(pure_vals)) if pure_vals else None,
        }
    lines.append("")

    # ============================================================
    # Verdict
    # ============================================================
    lines.append("## Verdict")
    lines.append("")
    bimodal_p = {axis: out["tests"]["bimodal"][axis]["p"] for axis in ("f1_paths_read", "f1_paths_written", "f1_hosts")}
    significant = [axis for axis, p in bimodal_p.items() if p is not None and p < 0.05]
    if significant:
        lines.append(f"**Bimodal split is statistically significant at α=0.05 on**: {', '.join(significant)}.")
        lines.append("")
        lines.append(
            "This converts the report's 'bimodal F1 distribution' claim from descriptive to "
            "formally tested. The CLI-wrapper cluster has a *significantly different* F1 distribution "
            "from the pure-text/single-output cluster, with the CLI-wrappers concentrated at the low end "
            "(Findings C, G) and pure-text skills at the high end."
        )
    else:
        lines.append("Bimodal split is not statistically significant at α=0.05 on any axis with available data; "
                     "the descriptive bimodal pattern persists but does not reach formal significance with this n.")

    out_dir = PROJECT_ROOT / "analysis"
    (out_dir / "subgroup-analysis.json").write_text(json.dumps(out, indent=2))
    (out_dir / "subgroup-analysis.md").write_text("\n".join(lines) + "\n")
    print(f"=> {out_dir}/subgroup-analysis.json")
    print(f"=> {out_dir}/subgroup-analysis.md")
    print()
    for s in lines:
        print(s)


if __name__ == "__main__":
    main()
