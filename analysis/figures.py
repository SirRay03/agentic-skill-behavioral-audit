#!/usr/bin/env python3
"""Phase 1.D — Visualizations for the report.

Generates 5 figures saved as SVG (vector — print-ready, embeddable in HTML):

  fig-01-f1-distribution.svg     — bimodal F1 histogram across n=29 with cluster annotations
  fig-02-predictor-variance.svg  — heatmap of orig×fresh×codex Jaccard per axis
  fig-03-pred-vs-obs.svg         — per-skill scatter of predicted vs observed host counts
  fig-04-ci-forest.svg           — forest plot of bootstrap 95% CIs for headline F1s
  fig-05-failure-modes.svg       — donut/sunburst-style breakdown of 24 hosts by category × declared/undeclared

Output: figures/*.svg (also rendered to .png at 200 DPI for portability)
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = PROJECT_ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)


def save(fig, name: str) -> None:
    svg_path = FIG_DIR / f"{name}.svg"
    png_path = FIG_DIR / f"{name}.png"
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"=> {svg_path}")


# ============================================================
# Figure 1: F1 distribution histogram (bimodal)
# ============================================================
def fig_f1_distribution() -> None:
    per_skill = json.loads((PROJECT_ROOT / "analysis" / "per-skill.json").read_text())
    f1s = []
    for r in per_skill:
        if "error" in r:
            continue
        v = r["fs_metrics"]["paths_read"]["f1"]
        if v is not None:
            f1s.append((r["skill_id"], v))

    f1s.sort(key=lambda x: x[1])
    skills = [s for s, _ in f1s]
    values = [v for _, v in f1s]

    fig, ax = plt.subplots(figsize=(10, 5))
    colours = ["#d33" if v < 0.10 else ("#3a7" if v >= 0.95 else "#888") for v in values]
    bars = ax.barh(range(len(skills)), values, color=colours, edgecolor="#333", linewidth=0.5)
    ax.set_yticks(range(len(skills)))
    ax.set_yticklabels(skills, fontsize=8)
    ax.set_xlabel("paths_read F1", fontsize=11)
    ax.set_xlim(-0.02, 1.05)
    ax.axvline(0.10, color="#d33", linestyle="--", alpha=0.5, linewidth=1)
    ax.axvline(0.95, color="#3a7", linestyle="--", alpha=0.5, linewidth=1)
    ax.set_title("Per-skill paths_read F1 — bimodal distribution\n"
                 "(left cluster F1<0.10: CLI-wrappers; right cluster F1≥0.95: pure-text/single-output)",
                 fontsize=11, pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.2)

    # Legend
    ax.scatter([], [], color="#d33", label="Low cluster (F1 < 0.10)", marker="s", s=80)
    ax.scatter([], [], color="#3a7", label="High cluster (F1 ≥ 0.95)", marker="s", s=80)
    ax.scatter([], [], color="#888", label="Middle", marker="s", s=80)
    ax.legend(loc="lower right", fontsize=9, frameon=False)

    save(fig, "fig-01-f1-distribution")


# ============================================================
# Figure 2: Predictor-variance heatmap
# ============================================================
def fig_predictor_variance() -> None:
    pv = json.loads((PROJECT_ROOT / "analysis" / "predictor-variance.json").read_text())
    summary = pv["summary"]
    axes_order = ["paths_read", "paths_written", "hosts", "subprocesses"]
    cmps = [("orig_vs_fresh", "orig vs fresh"),
            ("orig_vs_codex", "orig vs codex"),
            ("fresh_vs_codex", "fresh vs codex")]

    matrix = np.array([
        [summary[axis][cmp_key][0] or 0 for cmp_key, _ in cmps]
        for axis in axes_order
    ])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(cmps)))
    ax.set_xticklabels([c[1] for c in cmps], fontsize=10)
    ax.set_yticks(range(len(axes_order)))
    ax.set_yticklabels(axes_order, fontsize=10)

    for i in range(len(axes_order)):
        for j in range(len(cmps)):
            v = matrix[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=11, color=("white" if v < 0.4 else "black"), fontweight="bold")

    ax.set_title("Pairwise Jaccard similarity across three predictor sources\n"
                 "(higher = more agreement; n=25 production skills, fresh-batch)",
                 fontsize=11, pad=12)
    cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
    cbar.set_label("Jaccard similarity", fontsize=10)

    save(fig, "fig-02-predictor-variance")


# ============================================================
# Figure 3: predicted-vs-observed host count scatter
# ============================================================
def fig_pred_vs_obs_hosts() -> None:
    per_skill = json.loads((PROJECT_ROOT / "analysis" / "per-skill.json").read_text())
    points = []
    for r in per_skill:
        if "error" in r:
            continue
        sid = r["skill_id"]
        hosts = r["net_metrics"]["hosts"]
        n_pred = hosts.get("n_predicted", 0)
        n_obs = hosts.get("n_observed", 0)
        if n_pred == 0 and n_obs == 0:
            continue
        points.append((sid, n_pred, n_obs))

    fig, ax = plt.subplots(figsize=(8, 6))
    xs = [p[1] for p in points]
    ys = [p[2] for p in points]
    ax.scatter(xs, ys, s=80, alpha=0.7, edgecolor="#333", linewidth=0.7, color="#357")

    # 45-degree line
    lim = max(max(xs, default=0), max(ys, default=0)) + 1
    ax.plot([0, lim], [0, lim], "--", color="#888", alpha=0.6, label="perfect prediction (y=x)")

    # Annotate notable skills
    annotate_set = {"agent-browser", "wrangler", "firebase-hosting-basics", "semgrep",
                    "auth0-quickstart", "pinecone-mcp", "azure-validate", "cloudformation"}
    for sid, x, y in points:
        if sid in annotate_set:
            offset_y = 0.3 if (x, y) != (5, 5) else 0.7
            ax.annotate(sid, (x, y), xytext=(x + 0.3, y + offset_y), fontsize=8,
                        arrowprops=dict(arrowstyle="-", color="#888", alpha=0.5, lw=0.5))

    ax.set_xlabel("predicted hosts (predictor count)", fontsize=11)
    ax.set_ylabel("observed hosts (skill-attributable, agent-infra filtered)", fontsize=11)
    ax.set_title("Predicted vs Observed host count per skill\n"
                 "Above the line = under-prediction (Finding C/G); below = over-prediction",
                 fontsize=11, pad=12)
    ax.set_xlim(-0.5, lim)
    ax.set_ylim(-0.5, lim)
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.2)

    save(fig, "fig-03-pred-vs-obs")


# ============================================================
# Figure 4: forest plot of bootstrap 95% CIs
# ============================================================
def fig_ci_forest() -> None:
    stats = json.loads((PROJECT_ROOT / "analysis" / "stats.json").read_text())

    rows = [
        ("paths_read F1",   stats["f1_paths_read"]),
        ("paths_written F1", stats["f1_paths_written"]),
        ("hosts F1",         stats["f1_hosts"]),
    ]
    # Add cross-LLM headline
    if "jaccard_hosts_jacc_orig_fresh" in stats:
        rows.append(("Jaccard hosts: orig↔fresh-Claude", stats["jaccard_hosts_jacc_orig_fresh"]))
    if "jaccard_hosts_jacc_orig_codex" in stats:
        rows.append(("Jaccard hosts: orig-Claude↔Codex", stats["jaccard_hosts_jacc_orig_codex"]))

    fig, ax = plt.subplots(figsize=(9, 4.5))

    for i, (label, data) in enumerate(rows):
        m, lo, hi = data["mean"], data["ci_lo"], data["ci_hi"]
        ax.errorbar(m, i, xerr=[[m - lo], [hi - m]],
                    fmt="o", markersize=8, capsize=5, capthick=1.5,
                    color="#357", ecolor="#357", alpha=0.85)
        ax.annotate(f"{m:.3f} [{lo:.3f}, {hi:.3f}]",
                    (hi + 0.02, i), fontsize=9, va="center")

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.set_xlabel("estimate (95% bootstrap CI, 1000 resamples)", fontsize=11)
    ax.set_xlim(0, 1.05)
    ax.invert_yaxis()
    ax.set_title("Headline aggregate metrics with 95% bootstrap CIs\n"
                 "(seed 20260509; empty-vs-empty pairs excluded)",
                 fontsize=11, pad=12)
    ax.axvline(0.5, color="#888", linestyle=":", alpha=0.5, linewidth=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.2)

    save(fig, "fig-04-ci-forest")


# ============================================================
# Figure 5: failure-mode taxonomy donut + declared/undeclared bars
# ============================================================
def fig_failure_modes() -> None:
    tax = json.loads((PROJECT_ROOT / "analysis" / "failure-mode-taxonomy.json").read_text())
    cat_counts = tax["category_counts"]
    cat_dec = tax["category_declared"]
    cat_und = tax["category_undeclared"]

    # Stable category order (by count descending)
    cats = sorted(cat_counts.keys(), key=lambda c: -cat_counts[c])
    declared = [cat_dec[c] for c in cats]
    undeclared = [cat_und[c] for c in cats]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5),
                                    gridspec_kw={"width_ratios": [1, 1.2]})

    # ax1: donut
    sizes = [cat_counts[c] for c in cats]
    colors_palette = ["#d33", "#e88", "#f93", "#fc6", "#cd5", "#7c5", "#5b8"]
    wedges, texts, autotexts = ax1.pie(
        sizes, labels=cats, colors=colors_palette[:len(cats)],
        autopct="%1.0f%%", startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=9),
    )
    for at in autotexts:
        at.set_fontsize(9); at.set_fontweight("bold"); at.set_color("white")
    ax1.set_title(f"24 distinct skill-attributable hosts\nby failure-mode category", fontsize=11)

    # ax2: stacked bars declared vs undeclared
    y_pos = np.arange(len(cats))
    ax2.barh(y_pos, declared, color="#3a7", edgecolor="#333", linewidth=0.5, label="Declared (skill's own predictor named it)")
    ax2.barh(y_pos, undeclared, left=declared, color="#d33", edgecolor="#333", linewidth=0.5, label="Undeclared (Finding C/G)")
    for i, (d, u) in enumerate(zip(declared, undeclared)):
        if d > 0:
            ax2.text(d / 2, i, f"{d}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        if u > 0:
            ax2.text(d + u / 2, i, f"{u}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(cats, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("host count", fontsize=10)
    ax2.set_title("Declared vs undeclared per category\n(per-skill predictor matching)", fontsize=11)
    ax2.legend(loc="lower right", fontsize=9, frameon=False)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    save(fig, "fig-05-failure-modes")


# ============================================================
# Figure 6: Mutation suite 6×4 detection-rate heatmap
# ============================================================
def fig_mutation_suite() -> None:
    p = PROJECT_ROOT / "analysis" / "mutation-suite.json"
    if not p.exists():
        print("(skip fig-06: mutation-suite.json not yet present)")
        return
    data = json.loads(p.read_text())
    rows = data["per_mutation"]

    layers = ["L1_static", "L2_predictor", "L3_claude_runtime", "L4_codex_runtime"]
    layer_labels = ["L1 static\nregex", "L2 LLM\npredictor", "L3 Claude\nP4 runtime", "L4 Codex\nP4 runtime"]

    matrix = np.zeros((len(rows), len(layers)))
    for i, r in enumerate(rows):
        for j, layer in enumerate(layers):
            v = r[layer].get("caught")
            matrix[i, j] = 1.0 if v is True else (0.0 if v is False else 0.5)

    fig, ax = plt.subplots(figsize=(8, 5))
    cmap = plt.cm.RdYlGn
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels(layer_labels, fontsize=10)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r['code']} · {r['short']}" for r in rows], fontsize=9)

    for i in range(len(rows)):
        for j in range(len(layers)):
            v = matrix[i, j]
            symbol = "✓" if v == 1.0 else ("✗" if v == 0.0 else "?")
            ax.text(j, i, symbol, ha="center", va="center", fontsize=18,
                    color=("white" if v == 0.0 else "black"), fontweight="bold")

    # Per-layer rate annotation along top (as twin x-axis labels)
    layer_labels_with_rate = []
    for j, (layer, label) in enumerate(zip(layers, layer_labels)):
        caught_rate = matrix[:, j].mean()
        layer_labels_with_rate.append(f"{label}\n({caught_rate*100:.0f}% caught)")
    ax.set_xticklabels(layer_labels_with_rate, fontsize=10)

    ax.set_title("Mutation × Defense-Layer detection-rate table\n"
                 "(✓ caught / ✗ missed; per-layer rate in axis label)",
                 fontsize=11, pad=12)
    plt.tight_layout()
    save(fig, "fig-06-mutation-suite")


def main() -> None:
    fig_f1_distribution()
    fig_predictor_variance()
    fig_pred_vs_obs_hosts()
    fig_ci_forest()
    fig_failure_modes()
    fig_mutation_suite()


if __name__ == "__main__":
    main()
