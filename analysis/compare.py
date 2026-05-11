#!/usr/bin/env python3
"""P5 — Compare predicted vs observed capability footprints across all 25 skills.

For each skill: load `skills/<id>/prediction.json` (P3 output) and `skills/<id>/trace.json`
(P4 output). Filter out agent-infrastructure noise from observed traces. Compute
set-based metrics (precision/recall/F1, Jaccard) for paths and hosts. Stratify
qualitatively by skill category.

Outputs:
    analysis/per-skill.json     # detailed per-skill comparison
    analysis/summary.json       # aggregate metrics
    analysis/summary.md         # human-readable table for the report

Usage:
    python3 analysis/compare.py
"""
from __future__ import annotations
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Agent-infrastructure path predicates to FILTER OUT of the observed trace.
# These are paths that any claude invocation touches regardless of the loaded skill.
# Methodology §11 ("Trace blind spots") frames these as out-of-scope for the comparison.
AGENT_INFRA_PATH_PATTERNS = [
    r"^/usr/(?:lib|share|bin|sbin|local)(?:/|$)",
    r"^/proc(?:/|$)",
    r"^/dev(?:/|$)",
    r"^/sys(?:/|$)",
    r"^/etc(?:/|$)",
    r"^/run(?:/|$)",
    r"^/tmp/[A-Za-z0-9._-]+$",      # leaf files in /tmp (e.g. /tmp/foo.tmp), but NOT /tmp/work-*
    r"^/home/[^/]+/\.cache(?:/|$)",
    r"^/home/[^/]+/\.npm(?:/|$)",
    r"^/home/[^/]+/\.config/claude(?:-code)?(?:/|$)",
    r"^/home/[^/]+/\.claude/(?:cache|sessions|projects|backups|history|settings|\.credentials|plugins|local|file-history|todos|statsig|ide|debug)",
    r"^/home/[^/]+/\.claude\.json",
    r"^/home/[^/]+/\.config/configstore(?:/|$)",
    r"^/home/[^/]+/\.local/share/claude(?:/|$)",
    r"^/home/[^/]+/\.npm-global(?:/|$)",
    r"^/home/[^/]+/\.cargo(?:/|$)",
    r"node_modules/",                # any node_modules tree
    r"\.pyc$",
    r"^anon_inode:",                 # strace pseudo-paths
    r"^/etc/(?:passwd|group|nsswitch|resolv|host)",
]
AGENT_INFRA_RE = re.compile("|".join(AGENT_INFRA_PATH_PATTERNS))

# Agent-infrastructure hosts to FILTER OUT of observed trace.
AGENT_INFRA_HOSTS = {
    "api.anthropic.com",          # claude itself
    "statsig.anthropic.com",
    "console.anthropic.com",
    "telemetry.anthropic.com",
    "downloads.claude.ai",         # claude code update channel
    "mcp-proxy.anthropic.com",     # claude code MCP proxy
    "http-intake.logs.us5.datadoghq.com",  # claude code's telemetry vendor
    # Codex CLI (cross-agent runs)
    "chatgpt.com",
    "ab.chatgpt.com",
    "ipv4only.arpa",              # DNS quirk
    "localhost",
}


def is_skill_attributable_path(path: str) -> bool:
    """Decide whether an observed path is plausibly skill-attributable rather than
    agent infrastructure. Conservative: when in doubt, count it."""
    if AGENT_INFRA_RE.search(path):
        return False
    return True


def is_skill_attributable_host(host: str) -> bool:
    if not host or host in AGENT_INFRA_HOSTS:
        return False
    # Filter local/private addresses
    if host.startswith(("127.", "::1", "0.0.0.0")) or host == "localhost":
        return False
    if host.endswith(".local") or host.endswith(".arpa"):
        return False
    return True


def predicate_matches(observed: str, predicate: str) -> bool:
    """Match an observed concrete path/host against a predicate-style prediction.

    Predicates may include glob-like wildcards (* matches anything except path sep,
    ** matches across path seps). Predicates beginning with "./" are interpreted as
    workdir-relative and additionally match anywhere a corresponding suffix appears
    in observed paths (so "./rules/*.md" matches both "/tmp/work-x/rules/foo.md" and
    "/home/user/.claude/skills/x/rules/foo.md")."""
    if predicate == observed:
        return True
    # Convert predicate to regex
    p = re.escape(predicate)
    p = p.replace(r"\*\*", ".*")        # **
    p = p.replace(r"\*", "[^/]*")       # *
    p = p.replace(r"\~", r"(?:/home/[^/]+|~)")  # ~ -> /home/<user>
    # "./X" predicate: match an absolute path whose tail is "/X"
    if p.startswith(r"\./"):
        tail = p[len(r"\./"):]
        suffix_pattern = re.compile(r"(?:^|/)" + tail + r"$|(?:^|/)" + tail + r"/.*$")
        if suffix_pattern.search(observed):
            return True
    pattern = re.compile("^" + p + "$|^" + p + "/.*$")
    return bool(pattern.match(observed))


def host_matches(observed_host: str, predicate: str) -> bool:
    """Host match: exact, suffix, or wildcard."""
    if predicate == observed_host:
        return True
    if predicate.startswith("*."):
        suffix = predicate[2:]
        return observed_host.endswith("." + suffix) or observed_host == suffix
    # Treat any predicate without explicit prefix as a domain-suffix match
    if "." in predicate and not predicate.startswith("*"):
        return observed_host == predicate or observed_host.endswith("." + predicate)
    return False


def metrics(predicted: list[str], observed: list[str], match_fn) -> dict:
    """Compute precision/recall/F1/Jaccard for a predicted vs observed item set,
    using a custom predicate-match function (predicate_matches or host_matches)."""
    pred_set = set(predicted)
    obs_set = set(observed)

    # An observed item is "covered" if any predicate matches it.
    covered_obs = {o for o in obs_set if any(match_fn(o, p) for p in pred_set)}
    # A predicate is "useful" if it matches at least one observed item.
    useful_preds = {p for p in pred_set if any(match_fn(o, p) for o in obs_set)}

    tp = len(covered_obs)  # true positives (observed AND predicted)
    fn = len(obs_set) - tp  # false negatives (observed AND NOT predicted)
    # FP: predicates that didn't match any observed item. Note: predicate-style
    # predictions can match many observed items, so we count predicate-level FPs.
    fp = len(pred_set) - len(useful_preds)

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    jaccard = (
        len(covered_obs) / (len(covered_obs) + (len(obs_set) - tp) + (len(pred_set) - len(useful_preds)))
        if (len(obs_set) + len(pred_set)) > 0
        else None
    )

    return {
        "n_predicted": len(pred_set),
        "n_observed": len(obs_set),
        "n_covered": tp,
        "n_useful_predicates": len(useful_preds),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jaccard": jaccard,
        "false_negatives": sorted(obs_set - covered_obs)[:30],   # cap for readability
        "unmatched_predicates": sorted(pred_set - useful_preds)[:30],
    }


def compare_skill(skill_id: str) -> dict:
    skill_dir = PROJECT_ROOT / "skills" / skill_id
    pred_path = skill_dir / "prediction.json"
    trace_path = skill_dir / "trace.json"

    if not pred_path.exists():
        return {"skill_id": skill_id, "error": "prediction.json missing"}
    if not trace_path.exists():
        return {"skill_id": skill_id, "error": "trace.json missing"}

    pred = json.loads(pred_path.read_text(encoding="utf-8"))
    trace = json.loads(trace_path.read_text(encoding="utf-8"))

    fs = trace.get("fs", {})
    net = trace.get("net", {})

    obs_paths_read_all = fs.get("paths_read", [])
    obs_paths_written_all = fs.get("paths_written", [])
    obs_paths_deleted_all = fs.get("paths_deleted", [])
    obs_hosts_all = sorted({h for h in net.get("dns_queries", []) if h})

    # Filter agent infrastructure
    obs_paths_read = [p for p in obs_paths_read_all if is_skill_attributable_path(p)]
    obs_paths_written = [p for p in obs_paths_written_all if is_skill_attributable_path(p)]
    obs_paths_deleted = [p for p in obs_paths_deleted_all if is_skill_attributable_path(p)]
    obs_hosts = [h for h in obs_hosts_all if is_skill_attributable_host(h)]

    return {
        "skill_id": skill_id,
        "claude_exit": trace.get("claude_exit"),
        "duration_seconds": trace.get("duration_seconds"),
        "fs_metrics": {
            "paths_read": metrics(pred.get("paths_read", []), obs_paths_read, predicate_matches),
            "paths_written": metrics(pred.get("paths_written", []), obs_paths_written, predicate_matches),
            "paths_deleted": metrics(pred.get("paths_deleted", []), obs_paths_deleted, predicate_matches),
        },
        "net_metrics": {
            "hosts": metrics(pred.get("hosts", []), obs_hosts, host_matches),
        },
        "subprocess_predicted": pred.get("subprocesses", []),
        "rationale_predicted": pred.get("rationale", ""),
        "filter_stats": {
            "paths_read_total": len(obs_paths_read_all),
            "paths_read_after_filter": len(obs_paths_read),
            "paths_written_total": len(obs_paths_written_all),
            "paths_written_after_filter": len(obs_paths_written),
            "hosts_total": len(obs_hosts_all),
            "hosts_after_filter": len(obs_hosts),
        },
    }


def aggregate(results: list[dict]) -> dict:
    """Mean / median F1 across skills, stratified by skill category."""
    valid = [r for r in results if "error" not in r]

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return sum(xs) / len(xs) if xs else None

    def median(xs):
        xs = sorted(x for x in xs if x is not None)
        if not xs:
            return None
        n = len(xs)
        return (xs[n // 2 - 1] + xs[n // 2]) / 2 if n % 2 == 0 else xs[n // 2]

    f1_paths_read = [r["fs_metrics"]["paths_read"]["f1"] for r in valid]
    f1_paths_written = [r["fs_metrics"]["paths_written"]["f1"] for r in valid]
    f1_hosts = [r["net_metrics"]["hosts"]["f1"] for r in valid]

    return {
        "n_skills_compared": len(valid),
        "n_skills_errored": len(results) - len(valid),
        "f1_paths_read": {"mean": mean(f1_paths_read), "median": median(f1_paths_read)},
        "f1_paths_written": {"mean": mean(f1_paths_written), "median": median(f1_paths_written)},
        "f1_hosts": {"mean": mean(f1_hosts), "median": median(f1_hosts)},
    }


def fmt_f(v):
    return f"{v:.3f}" if v is not None else "—"


def render_summary_md(results: list[dict], agg: dict) -> str:
    lines = [
        "# Comparison Summary",
        "",
        f"**Skills compared**: {agg['n_skills_compared']} / {agg['n_skills_compared'] + agg['n_skills_errored']}",
        "",
        "## Aggregate F1 (predicted-vs-observed, predicate-style match)",
        "",
        "| Dimension | Mean F1 | Median F1 |",
        "|---|---|---|",
        f"| paths_read   | {fmt_f(agg['f1_paths_read']['mean'])} | {fmt_f(agg['f1_paths_read']['median'])} |",
        f"| paths_written| {fmt_f(agg['f1_paths_written']['mean'])} | {fmt_f(agg['f1_paths_written']['median'])} |",
        f"| hosts        | {fmt_f(agg['f1_hosts']['mean'])} | {fmt_f(agg['f1_hosts']['median'])} |",
        "",
        "## Per-skill F1",
        "",
        "| Skill | claude exit | duration | paths_read F1 | paths_written F1 | hosts F1 |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['skill_id']} | ERR | — | — | — | — |")
            continue

        def f(m, key):
            v = m[key]["f1"]
            return f"{v:.2f}" if v is not None else "—"

        lines.append(
            f"| {r['skill_id']} | {r['claude_exit']} | {r['duration_seconds']}s | "
            f"{f(r['fs_metrics'], 'paths_read')} | {f(r['fs_metrics'], 'paths_written')} | "
            f"{f(r['net_metrics'], 'hosts')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    skill_ids = [d.name for d in (PROJECT_ROOT / "skills").iterdir() if d.is_dir()]
    skill_ids.sort()

    results = [compare_skill(s) for s in skill_ids]
    agg = aggregate(results)

    out_dir = PROJECT_ROOT / "analysis"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "per-skill.json").write_text(json.dumps(results, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(agg, indent=2))
    (out_dir / "summary.md").write_text(render_summary_md(results, agg))

    print(json.dumps(agg, indent=2))
    print()
    print(f"=> {out_dir}/per-skill.json")
    print(f"=> {out_dir}/summary.json")
    print(f"=> {out_dir}/summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
