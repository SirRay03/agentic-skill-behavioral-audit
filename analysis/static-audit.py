#!/usr/bin/env python3
"""Static SKILL.md analysis baseline (Enrichment 4).

For each skill, regex-scan SKILL.md for declared hosts, subprocesses, and suspicious
patterns. Compare against dynamic observations (trace.json) and the LLM predictor's
output (prediction.json). Report static-vs-dynamic and static-vs-LLM gaps.

Output:
  analysis/static-per-skill.json   — full static findings per skill
  analysis/static-vs-dynamic.md    — comparison table for the report

Usage:
    python3 analysis/static-audit.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"

# Hosts to deliberately ignore in static extraction (commonplace, not informative)
HOST_BLACKLIST = {
    "example.com", "localhost", "your-domain.com", "yoursite.com",
    "mysite.com", "github.com",  # github.com appears in nearly every SKILL.md as a citation
    # Documentation hosts
    "docs.docker.com", "docs.npmjs.com",
}

# Regex patterns for static extraction
URL_PATTERN = re.compile(
    r"https?://([a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,})(?:[/:][^\s\)\]'\"]*)?",
    re.IGNORECASE,
)

# Code-block contents (fenced ``` ... ``` blocks)
CODE_BLOCK_PATTERN = re.compile(r"```(?:\w+)?\n(.*?)\n```", re.DOTALL)
# Inline backticks
INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")

# Suspicious shell command patterns to flag
SUSPICIOUS_PATTERNS = [
    (r"\bcurl\b[^\n]*-X\s+POST", "curl-post"),
    (r"\bcurl\b[^\n]*-d\s", "curl-with-data"),
    (r"\bwget\b[^\n]*\|", "wget-pipe-to-shell"),
    (r"\|\s*(?:bash|sh|python3?)\b", "pipe-to-shell"),
    (r"\bsudo\b", "sudo-required"),
    (r"\brm\s+-rf\s+/", "rm-rf-root"),
    (r"\bbase64\b[^\n]*\|", "base64-pipe"),
    (r"(?:^|\s)cat\s+[^|]+\|\s*curl\b", "exfil-pattern-cat-pipe-curl"),
    (r"-H\s+['\"]?Authorization", "auth-header"),
    (r"\$\([^)]*\)", "command-substitution"),
]

# Common subprocess binary names to detect mentions of
COMMON_BINARIES = [
    "npm", "npx", "node", "python", "python3", "pip", "pip3",
    "curl", "wget", "git", "gh",
    "wrangler", "firebase", "firecrawl", "agent-browser", "vercel",
    "aws", "gcloud", "az", "azd", "bicep", "terraform",
    "prisma", "semgrep", "swift", "xcode-select", "xcodebuild",
    "docker", "kubectl",
]
BINARY_PATTERN = re.compile(
    r"(?:^|[\s`])(" + "|".join(re.escape(b) for b in COMMON_BINARIES) + r")(?:\s|`|$)"
)


def extract_static(skill_md: str) -> dict:
    """Pull out hosts, subprocesses, and suspicious flags from SKILL.md text."""
    # Hosts: collect all URLs, dedup, drop blacklisted
    hosts = set()
    for match in URL_PATTERN.finditer(skill_md):
        host = match.group(1).lower()
        if host in HOST_BLACKLIST:
            continue
        # Strip leading "www." for normalization
        normalized = host[4:] if host.startswith("www.") else host
        hosts.add(normalized)

    # Subprocesses: scan inline code + code blocks for known binary tokens
    code_text = " ".join(CODE_BLOCK_PATTERN.findall(skill_md))
    code_text += " " + " ".join(INLINE_CODE_PATTERN.findall(skill_md))
    subprocesses = set(BINARY_PATTERN.findall(code_text))

    # Suspicious patterns: scan whole text
    suspicious = []
    for pattern, label in SUSPICIOUS_PATTERNS:
        if re.search(pattern, skill_md, re.MULTILINE):
            suspicious.append(label)

    return {
        "hosts": sorted(hosts),
        "subprocesses": sorted(subprocesses),
        "suspicious_patterns": sorted(suspicious),
    }


def host_set(predicates: list[str]) -> set[str]:
    """Normalise a list of host predicates (e.g. '*.firecrawl.dev', 'api.firecrawl.dev')
    to a set of bare-domain strings for set comparison."""
    out = set()
    for p in predicates:
        p = p.lower()
        if p.startswith("*."):
            p = p[2:]
        out.add(p)
    return out


def main() -> int:
    skill_ids = sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir())
    rows = []
    for sid in skill_ids:
        sd = SKILLS_DIR / sid
        skill_md_path = sd / "SKILL.md"
        if not skill_md_path.exists():
            continue
        skill_md = skill_md_path.read_text(encoding="utf-8")
        static = extract_static(skill_md)

        prediction_path = sd / "prediction.json"
        trace_path = sd / "trace.json"
        pred = json.loads(prediction_path.read_text()) if prediction_path.exists() else {}
        trace = json.loads(trace_path.read_text()) if trace_path.exists() else {}

        observed_hosts = set()
        if trace and "net" in trace:
            for h in trace["net"].get("dns_queries", []):
                observed_hosts.add(h.lower())
        # Filter agent infra hosts (same list as compare.py)
        AGENT_INFRA = {
            "api.anthropic.com", "downloads.claude.ai", "mcp-proxy.anthropic.com",
            "http-intake.logs.us5.datadoghq.com", "chatgpt.com", "ab.chatgpt.com",
            "ipv4only.arpa", "localhost",
        }
        observed_hosts -= AGENT_INFRA

        static_hosts = set(static["hosts"])
        llm_hosts = host_set(pred.get("hosts", []))

        def covers(superset, target_host):
            if target_host in superset:
                return True
            for s in superset:
                if target_host == s or target_host.endswith("." + s):
                    return True
            return False

        static_caught = {h for h in observed_hosts if covers(static_hosts, h)}
        llm_caught = {h for h in observed_hosts if covers(llm_hosts, h)}

        rows.append({
            "skill_id": sid,
            "static_hosts": sorted(static_hosts),
            "llm_predicted_hosts": sorted(llm_hosts),
            "observed_hosts": sorted(observed_hosts),
            "static_caught_dynamic": sorted(static_caught),
            "llm_caught_dynamic": sorted(llm_caught),
            "static_recall": len(static_caught) / len(observed_hosts) if observed_hosts else None,
            "llm_recall":    len(llm_caught)    / len(observed_hosts) if observed_hosts else None,
            "suspicious_patterns": static["suspicious_patterns"],
            "static_subprocesses": static["subprocesses"],
        })

    # Summary
    skills_with_obs = [r for r in rows if r["static_recall"] is not None]
    n = len(skills_with_obs)
    static_avg = sum(r["static_recall"] for r in skills_with_obs) / n if n else 0
    llm_avg = sum(r["llm_recall"] for r in skills_with_obs) / n if n else 0

    out_dir = PROJECT_ROOT / "analysis"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "static-per-skill.json").write_text(json.dumps(rows, indent=2))

    # Markdown table
    lines = [
        "# Static SKILL.md analysis vs. Dynamic Observation vs. LLM Prediction",
        "",
        f"Skills compared (with non-empty observed hosts): {n} / {len(rows)}",
        "",
        f"**Mean recall against observed hosts**:",
        f"- Static regex baseline: **{static_avg:.3f}**",
        f"- LLM (xhigh) prediction: **{llm_avg:.3f}**",
        "",
        "## Per-skill table",
        "",
        "| Skill | observed | static found | LLM found | static recall | LLM recall | suspicious flags |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        nobs = len(r["observed_hosts"])
        nstatic = len(r["static_caught_dynamic"])
        nllm = len(r["llm_caught_dynamic"])
        sr = f"{r['static_recall']:.2f}" if r["static_recall"] is not None else "—"
        lr = f"{r['llm_recall']:.2f}" if r["llm_recall"] is not None else "—"
        flags = ",".join(r["suspicious_patterns"]) or "-"
        lines.append(f"| {r['skill_id']} | {nobs} | {nstatic} | {nllm} | {sr} | {lr} | {flags} |")

    (out_dir / "static-vs-dynamic.md").write_text("\n".join(lines) + "\n")
    print(f"static recall mean: {static_avg:.3f}")
    print(f"llm recall mean:    {llm_avg:.3f}")
    print(f"=> {out_dir}/static-per-skill.json")
    print(f"=> {out_dir}/static-vs-dynamic.md")
    return 0


if __name__ == "__main__":
    main()
