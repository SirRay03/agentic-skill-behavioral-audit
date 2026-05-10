#!/usr/bin/env python3
"""Compute F1 for each of the three predictor sources against the SAME observed traces.

Currently the report uses `skills/<id>/prediction.json` (orig-Claude with project
context, xhigh) as source of truth. The fresh-Claude and Codex predictions live
under /tmp/fresh-predictor-batch/outputs/. Run compare.py-equivalent matching against
each prediction source independently and aggregate.

Output: analysis/predictor-vs-truth.json + .md
"""
from __future__ import annotations
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRESH_ROOT = Path("/tmp/fresh-predictor-batch")

# Same agent-infra filter as compare.py v4
AGENT_INFRA_PATH_PATTERNS = [
    r"^/usr/(?:lib|share|bin|sbin|local)(?:/|$)",
    r"^/proc(?:/|$)", r"^/dev(?:/|$)", r"^/sys(?:/|$)",
    r"^/etc(?:/|$)", r"^/run(?:/|$)",
    r"^/tmp/[A-Za-z0-9._-]+$",
    r"^/home/[^/]+/\.cache(?:/|$)",
    r"^/home/[^/]+/\.npm(?:/|$)",
    r"^/home/[^/]+/\.config/claude(?:-code)?(?:/|$)",
    r"^/home/[^/]+/\.claude/(?:cache|sessions|projects|backups|history|settings|\.credentials|plugins|local|file-history|todos|statsig|ide|debug)",
    r"^/home/[^/]+/\.claude\.json",
    r"^/home/[^/]+/\.config/configstore(?:/|$)",
    r"^/home/[^/]+/\.local/share/claude(?:/|$)",
    r"^/home/[^/]+/\.npm-global(?:/|$)",
    r"^/home/[^/]+/\.cargo(?:/|$)",
    r"node_modules/", r"\.pyc$", r"^anon_inode:",
    r"^/etc/(?:passwd|group|nsswitch|resolv|host)",
]
AGENT_INFRA_RE = re.compile("|".join(AGENT_INFRA_PATH_PATTERNS))

AGENT_INFRA_HOSTS = {
    "api.anthropic.com", "downloads.claude.ai", "mcp-proxy.anthropic.com",
    "http-intake.logs.us5.datadoghq.com", "chatgpt.com", "ab.chatgpt.com",
    "ipv4only.arpa", "localhost",
}


def is_skill_path(p: str) -> bool:
    if AGENT_INFRA_RE.search(p):
        return False
    return True


def is_skill_host(h: str) -> bool:
    if not h or h in AGENT_INFRA_HOSTS:
        return False
    if h.startswith(("127.", "::1", "0.0.0.0")) or h == "localhost":
        return False
    if h.endswith(".local") or h.endswith(".arpa"):
        return False
    return True


def predicate_matches(observed: str, predicate: str) -> bool:
    if predicate == observed:
        return True
    p = re.escape(predicate)
    p = p.replace(r"\*\*", ".*")
    p = p.replace(r"\*", "[^/]*")
    p = p.replace(r"\~", r"(?:/home/[^/]+|~)")
    if p.startswith(r"\./"):
        tail = p[len(r"\./"):]
        suffix_pat = re.compile(r"(?:^|/)" + tail + r"$|(?:^|/)" + tail + r"/.*$")
        if suffix_pat.search(observed):
            return True
    pattern = re.compile("^" + p + "$|^" + p + "/.*$")
    return bool(pattern.match(observed))


def host_matches(observed: str, predicate: str) -> bool:
    if predicate == observed:
        return True
    if predicate.startswith("*."):
        suffix = predicate[2:]
        return observed.endswith("." + suffix) or observed == suffix
    if "." in predicate and not predicate.startswith("*"):
        return observed == predicate or observed.endswith("." + predicate)
    return False


def f1(predicted: list[str], observed: list[str], match_fn) -> float | None:
    pred_set = set(predicted)
    obs_set = set(observed)
    covered = {o for o in obs_set if any(match_fn(o, p) for p in pred_set)}
    useful = {p for p in pred_set if any(match_fn(o, p) for o in obs_set)}
    tp = len(covered)
    fn = len(obs_set) - tp
    fp = len(pred_set) - len(useful)
    prec = tp / (tp + fp) if (tp + fp) > 0 else None
    rec = tp / (tp + fn) if (tp + fn) > 0 else None
    if prec is None or rec is None or (prec + rec) == 0:
        return None
    return 2 * prec * rec / (prec + rec)


def main():
    skills_dir = PROJECT_ROOT / "skills"
    skill_ids = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
    # Only production skills: exclude *-aug and zz-* (mutation/adversarial)
    skill_ids = [s for s in skill_ids if not s.endswith("-aug") and not s.startswith("zz-")]

    # Repo-relative paths (preferred); fall back to /tmp/fresh-predictor-batch/ for
    # backward compatibility with the original execution environment.
    def fresh_path(sid):
        repo = skills_dir / sid / "prediction-fresh.json"
        return repo if repo.exists() else FRESH_ROOT / "outputs" / "claude-fresh" / sid / "prediction-fresh.json"
    def codex_path(sid):
        repo = skills_dir / sid / "prediction-codex.json"
        return repo if repo.exists() else FRESH_ROOT / "outputs" / "codex-fresh" / sid / "prediction-codex.json"
    predictor_paths = {
        "orig":  lambda sid: skills_dir / sid / "prediction.json",
        "fresh": fresh_path,
        "codex": codex_path,
    }

    results = {p: {"per_skill": {}} for p in predictor_paths}
    n_skills = 0

    for sid in skill_ids:
        trace_path = skills_dir / sid / "trace.json"
        if not trace_path.exists():
            continue
        n_skills += 1
        trace = json.loads(trace_path.read_text())
        fs = trace.get("fs", {})
        net = trace.get("net", {})
        obs_paths_read    = [p for p in fs.get("paths_read", [])    if is_skill_path(p)]
        obs_paths_written = [p for p in fs.get("paths_written", []) if is_skill_path(p)]
        obs_hosts         = sorted({h for h in net.get("dns_queries", []) if h and is_skill_host(h)})

        for predictor in predictor_paths:
            pp = predictor_paths[predictor](sid)
            if not pp.exists():
                continue
            try:
                pred = json.loads(pp.read_text())
            except json.JSONDecodeError:
                continue
            results[predictor]["per_skill"][sid] = {
                "f1_paths_read":    f1(pred.get("paths_read", []),    obs_paths_read,    predicate_matches),
                "f1_paths_written": f1(pred.get("paths_written", []), obs_paths_written, predicate_matches),
                "f1_hosts":         f1(pred.get("hosts", []),         obs_hosts,         host_matches),
            }

    # Aggregate
    summary = {}
    for predictor in predictor_paths:
        per = results[predictor]["per_skill"]
        for axis in ("f1_paths_read", "f1_paths_written", "f1_hosts"):
            values = [v[axis] for v in per.values() if v[axis] is not None]
            mean = sum(values) / len(values) if values else None
            summary.setdefault(axis, {})[predictor] = {
                "n": len(values),
                "mean": mean,
                "values": values,
            }

    # Markdown
    lines = [
        "# Predictor-vs-Truth: F1 per predictor source against same observed traces",
        "",
        f"Skills compared: {n_skills} production skills (excluding *-aug and zz-*).",
        "Each predictor scored against the same `trace.json` per skill, with the same",
        "v4 agent-infra filter applied to observed paths/hosts.",
        "",
        "## Aggregate mean F1 per axis × predictor",
        "",
        "| Axis | orig-Claude (n) | fresh-Claude (n) | Codex (n) |",
        "|---|---|---|---|",
    ]
    for axis_pretty, axis_key in [("paths_read", "f1_paths_read"),
                                   ("paths_written", "f1_paths_written"),
                                   ("hosts", "f1_hosts")]:
        cells = []
        for predictor in ("orig", "fresh", "codex"):
            s = summary[axis_key][predictor]
            if s["mean"] is None:
                cells.append("—")
            else:
                cells.append(f"**{s['mean']:.3f}** (n={s['n']})")
        lines.append(f"| {axis_pretty} | {cells[0]} | {cells[1]} | {cells[2]} |")

    # Per-skill side-by-side (hosts axis only, for readability)
    lines.extend([
        "",
        "## Per-skill F1 — hosts axis (most stable, key headline)",
        "",
        "| Skill | orig | fresh | codex |",
        "|---|---|---|---|",
    ])
    all_skill_ids = sorted(set(
        sid for predictor in results
        for sid in results[predictor]["per_skill"]
    ))
    for sid in all_skill_ids:
        cells = []
        for predictor in ("orig", "fresh", "codex"):
            v = results[predictor]["per_skill"].get(sid, {}).get("f1_hosts")
            cells.append(f"{v:.2f}" if v is not None else "—")
        lines.append(f"| {sid} | {cells[0]} | {cells[1]} | {cells[2]} |")

    # Find which predictor wins per axis
    lines.extend(["", "## Verdict", ""])
    for axis_pretty, axis_key in [("paths_read", "f1_paths_read"),
                                   ("paths_written", "f1_paths_written"),
                                   ("hosts", "f1_hosts")]:
        means = {p: summary[axis_key][p]["mean"] for p in ("orig", "fresh", "codex")
                 if summary[axis_key][p]["mean"] is not None}
        if not means:
            continue
        winner = max(means, key=means.get)
        spread = max(means.values()) - min(means.values())
        lines.append(f"- **{axis_pretty}**: best is **{winner}** ({means[winner]:.3f}); "
                     f"spread across predictors = {spread:.3f}")

    out_dir = PROJECT_ROOT / "analysis"
    (out_dir / "predictor-vs-truth.json").write_text(json.dumps({"summary": summary, "results": results, "n_skills": n_skills}, indent=2))
    (out_dir / "predictor-vs-truth.md").write_text("\n".join(lines) + "\n")
    print(f"=> {out_dir}/predictor-vs-truth.json")
    print(f"=> {out_dir}/predictor-vs-truth.md")
    print()
    for axis_pretty, axis_key in [("paths_read", "f1_paths_read"),
                                   ("paths_written", "f1_paths_written"),
                                   ("hosts", "f1_hosts")]:
        cells = []
        for predictor in ("orig", "fresh", "codex"):
            s = summary[axis_key][predictor]
            cells.append(f"{predictor}={s['mean']:.3f} (n={s['n']})" if s['mean'] is not None else f"{predictor}=—")
        print(f"  {axis_pretty:<15s}: {' | '.join(cells)}")


if __name__ == "__main__":
    main()
