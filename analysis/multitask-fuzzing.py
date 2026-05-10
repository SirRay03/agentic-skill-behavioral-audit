#!/usr/bin/env python3
"""Phase 3.L — Multi-task fuzzing analysis.

For each of {wrangler, semgrep, firebase-hosting-basics}, three task prompts:
  - original task.md (existing trace.json at high effort)
  - alt1 (alternate documented verb, trace-l-alt1.json)
  - alt2 (alternate documented verb, trace-l-alt2.json)

Compute:
  - hosts F1 per (skill, prompt) cell against the same prediction.json
  - hosts-set Jaccard between the three prompts of the same skill (does the
    prompt change WHICH hosts are observed?)
  - aggregate F1 spread per skill — is the original-prompt F1 representative?

Output: analysis/multitask-fuzzing.{json,md}
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_INFRA = {
    "api.anthropic.com", "downloads.claude.ai", "mcp-proxy.anthropic.com",
    "http-intake.logs.us5.datadoghq.com", "chatgpt.com", "ab.chatgpt.com",
    "ipv4only.arpa", "localhost",
}


def host_matches(observed: str, predicate: str) -> bool:
    if predicate == observed:
        return True
    if predicate.startswith("*."):
        suffix = predicate[2:]
        return observed.endswith("." + suffix) or observed == suffix
    if "." in predicate and not predicate.startswith("*"):
        return observed == predicate or observed.endswith("." + predicate)
    return False


def f1_hosts(predicted: list[str], observed: list[str]) -> float | None:
    pred = {p.lower() for p in predicted}
    obs = {o.lower() for o in observed}
    if not pred and not obs:
        return None
    covered = {o for o in obs if any(host_matches(o, p) for p in pred)}
    useful = {p for p in pred if any(host_matches(o, p) for o in obs)}
    tp = len(covered)
    fn = len(obs) - tp
    fp = len(pred) - len(useful)
    prec = tp / (tp + fp) if (tp + fp) > 0 else None
    rec = tp / (tp + fn) if (tp + fn) > 0 else None
    if prec is None or rec is None or (prec + rec) == 0:
        return None
    return 2 * prec * rec / (prec + rec)


def load_obs_hosts(trace_path: Path) -> set[str] | None:
    if not trace_path.exists():
        return None
    t = json.loads(trace_path.read_text())
    return {h.lower() for h in t.get("net", {}).get("dns_queries", []) if h.lower() not in AGENT_INFRA}


def jaccard(a: set, b: set) -> float | None:
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main():
    sd_root = PROJECT_ROOT / "skills"
    out_lines = ["# Phase 3.L — Multi-task fuzzing", "", ]
    out_lines.append("Three documented-verb prompt variants per skill (original, alt1, alt2).")
    out_lines.append("Hosts F1 against the same prediction.json + pairwise Jaccard between prompt-driven host sets.")
    out_lines.append("")

    out_lines.append("| Skill | Original F1 | alt1 F1 | alt2 F1 | F1 spread | mean inter-prompt host-set Jaccard |")
    out_lines.append("|---|---|---|---|---|---|")

    summary = {}
    for sid in ("wrangler", "semgrep", "firebase-hosting-basics"):
        sd = sd_root / sid
        pred = json.loads((sd / "prediction.json").read_text())
        pred_hosts = pred.get("hosts", [])

        results = {}
        host_sets = {}
        for label, fname in [("original", "trace.json"),
                              ("alt1",     "trace-l-alt1.json"),
                              ("alt2",     "trace-l-alt2.json")]:
            obs = load_obs_hosts(sd / fname)
            host_sets[label] = obs
            if obs is None:
                results[label] = None
                continue
            results[label] = f1_hosts(pred_hosts, list(obs))

        valid_f1 = [v for v in results.values() if v is not None]
        spread = max(valid_f1) - min(valid_f1) if len(valid_f1) >= 2 else None

        # pairwise host-set Jaccard
        labels = ["original", "alt1", "alt2"]
        jaccs = []
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a, b = host_sets[labels[i]], host_sets[labels[j]]
                if a is not None and b is not None:
                    jv = jaccard(a, b)
                    if jv is not None:
                        jaccs.append(jv)
        mean_j = float(np.mean(jaccs)) if jaccs else None

        summary[sid] = {
            "f1_per_prompt": results,
            "host_sets_per_prompt": {k: sorted(v) if v is not None else None for k, v in host_sets.items()},
            "f1_spread": spread,
            "mean_inter_prompt_jaccard": mean_j,
        }

        def fmt(v): return f"{v:.3f}" if v is not None else "—"
        out_lines.append(
            f"| {sid} | {fmt(results['original'])} | {fmt(results['alt1'])} | {fmt(results['alt2'])} | "
            f"{fmt(spread)} | {fmt(mean_j)} |"
        )

    spreads = [v["f1_spread"] for v in summary.values() if v["f1_spread"] is not None]
    jaccs_all = [v["mean_inter_prompt_jaccard"] for v in summary.values() if v["mean_inter_prompt_jaccard"] is not None]

    if spreads:
        out_lines.append("")
        out_lines.append(f"**Aggregate** — mean F1 spread across prompts: **{np.mean(spreads):.3f}** (n={len(spreads)} skills with all 3 prompts traced).")
        out_lines.append("")
        out_lines.append(f"**Mean inter-prompt host-set Jaccard**: **{np.mean(jaccs_all):.3f}** (n={len(jaccs_all)} skills).")

    out_lines.append("")
    out_lines.append("## Per-skill detail")
    out_lines.append("")
    for sid, s in summary.items():
        out_lines.append(f"### {sid}")
        out_lines.append("")
        for label, hosts in s["host_sets_per_prompt"].items():
            if hosts is None:
                out_lines.append(f"- **{label}**: trace not found")
            else:
                out_lines.append(f"- **{label}** (F1={s['f1_per_prompt'][label]}): {hosts}")
        out_lines.append("")

    out_dir = PROJECT_ROOT / "analysis"
    (out_dir / "multitask-fuzzing.json").write_text(json.dumps(summary, indent=2, default=lambda o: list(o) if isinstance(o, set) else o))
    (out_dir / "multitask-fuzzing.md").write_text("\n".join(out_lines) + "\n")
    print(f"=> {out_dir}/multitask-fuzzing.json")
    print(f"=> {out_dir}/multitask-fuzzing.md")


if __name__ == "__main__":
    main()
