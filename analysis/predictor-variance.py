#!/usr/bin/env python3
"""Compare three prediction sources per skill:

  1. prediction.json            — original Claude Opus 4.7 xhigh, full project context
  2. prediction-fresh.json      — same Claude model, clean $HOME (no plugins/memory/skills)
  3. prediction-codex.json      — OpenAI Codex CLI (GPT-family), clean $HOME

For each skill and each axis (hosts, paths_read, paths_written, subprocesses),
compute pairwise Jaccard similarity between the three prediction sets.

Aggregates:
  - Mean Jaccard(orig, fresh)   — measures context-contamination effect
  - Mean Jaccard(orig, codex)   — measures cross-LLM variance
  - Mean Jaccard(fresh, codex)  — same-context cross-LLM variance (cleanest)

Outputs:
  analysis/predictor-variance.json
  analysis/predictor-variance.md
"""
from __future__ import annotations
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRESH_ROOT = Path(os.environ.get("FRESH", "/tmp/fresh-predictor-batch"))


def normalize(items: list[str]) -> set[str]:
    return {s.lower().strip() for s in (items or []) if s and s.strip()}


def jaccard(a: set, b: set) -> float | None:
    if not a and not b:
        return None  # undefined for empty-vs-empty
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_pred(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def main() -> int:
    rows = []
    skill_ids = sorted(d.name for d in (FRESH_ROOT / "skills").iterdir() if d.is_dir())

    for sid in skill_ids:
        orig = load_pred(PROJECT_ROOT / "skills" / sid / "prediction.json")
        # Prefer repo-relative paths (post-relocation); fall back to /tmp.
        fresh_repo = PROJECT_ROOT / "skills" / sid / "prediction-fresh.json"
        codex_repo = PROJECT_ROOT / "skills" / sid / "prediction-codex.json"
        fresh = load_pred(fresh_repo) or load_pred(FRESH_ROOT / "outputs" / "claude-fresh" / sid / "prediction-fresh.json")
        codex = load_pred(codex_repo) or load_pred(FRESH_ROOT / "outputs" / "codex-fresh" / sid / "prediction-codex.json")
        if not (orig and fresh and codex):
            rows.append({
                "skill_id": sid,
                "missing": [n for n, v in [("orig", orig), ("fresh", fresh), ("codex", codex)] if not v],
            })
            continue

        per_axis = {}
        for axis in ("paths_read", "paths_written", "paths_deleted", "hosts", "subprocesses"):
            o = normalize(orig.get(axis, []))
            f = normalize(fresh.get(axis, []))
            c = normalize(codex.get(axis, []))
            per_axis[axis] = {
                "n_orig": len(o),
                "n_fresh": len(f),
                "n_codex": len(c),
                "jacc_orig_fresh": jaccard(o, f),
                "jacc_orig_codex": jaccard(o, c),
                "jacc_fresh_codex": jaccard(f, c),
            }

        rows.append({"skill_id": sid, "axes": per_axis})

    # Aggregates
    valid = [r for r in rows if "axes" in r]

    def agg(axis: str, key: str) -> tuple[float | None, float | None, int]:
        vs = [r["axes"][axis][key] for r in valid if r["axes"][axis][key] is not None]
        if not vs:
            return (None, None, 0)
        return (sum(vs) / len(vs), sorted(vs)[len(vs) // 2], len(vs))

    summary = {}
    for axis in ("paths_read", "paths_written", "hosts", "subprocesses"):
        summary[axis] = {
            "orig_vs_fresh": agg(axis, "jacc_orig_fresh"),
            "orig_vs_codex": agg(axis, "jacc_orig_codex"),
            "fresh_vs_codex": agg(axis, "jacc_fresh_codex"),
        }

    out_dir = PROJECT_ROOT / "analysis"
    (out_dir / "predictor-variance.json").write_text(json.dumps(
        {"summary": summary, "per_skill": rows}, indent=2,
    ))

    # Markdown
    lines = [
        "# Predictor Variance: original-Claude vs fresh-Claude vs Codex",
        "",
        f"Skills with all three prediction sources: {len(valid)} / {len(rows)}",
        "",
        "## Aggregate mean Jaccard similarity",
        "",
        "Higher Jaccard = more agreement on which items are predicted. Empty-vs-empty pairs",
        "are excluded from the mean (jaccard undefined).",
        "",
        "| axis | orig vs fresh | orig vs codex | fresh vs codex | n |",
        "|---|---|---|---|---|",
    ]
    for axis, vals in summary.items():
        of_m = vals["orig_vs_fresh"][0]
        oc_m = vals["orig_vs_codex"][0]
        fc_m = vals["fresh_vs_codex"][0]
        n = max(vals["orig_vs_fresh"][2], vals["orig_vs_codex"][2], vals["fresh_vs_codex"][2])
        def fmt(v): return f"{v:.3f}" if v is not None else "—"
        lines.append(f"| {axis} | {fmt(of_m)} | {fmt(oc_m)} | {fmt(fc_m)} | {n} |")

    lines.extend([
        "",
        "## Per-skill detail (hosts axis only, for brevity)",
        "",
        "| skill | n_orig | n_fresh | n_codex | jacc(o,f) | jacc(o,c) | jacc(f,c) |",
        "|---|---|---|---|---|---|---|",
    ])
    for r in rows:
        if "axes" not in r:
            lines.append(f"| {r['skill_id']} | _missing: {','.join(r['missing'])}_ | | | | | |")
            continue
        h = r["axes"]["hosts"]
        def f(v): return f"{v:.2f}" if v is not None else "—"
        lines.append(
            f"| {r['skill_id']} | {h['n_orig']} | {h['n_fresh']} | {h['n_codex']} | "
            f"{f(h['jacc_orig_fresh'])} | {f(h['jacc_orig_codex'])} | {f(h['jacc_fresh_codex'])} |"
        )

    (out_dir / "predictor-variance.md").write_text("\n".join(lines) + "\n")
    print(f"=> {out_dir}/predictor-variance.json")
    print(f"=> {out_dir}/predictor-variance.md")
    print()
    for axis, vals in summary.items():
        print(f"{axis}: orig-fresh={vals['orig_vs_fresh'][0]} orig-codex={vals['orig_vs_codex'][0]} fresh-codex={vals['fresh_vs_codex'][0]}")


if __name__ == "__main__":
    main()
