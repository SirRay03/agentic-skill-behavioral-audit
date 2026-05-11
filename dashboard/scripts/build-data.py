#!/usr/bin/env python3
"""
build-data.py — Read the audit repo and emit structured JSON for Astro.

Walks ../../skills/, ../../analysis/, ../../report.md and emits to
src/data/generated/. Idempotent; safe to run repeatedly.

The dashboard does NOT modify any audit content. Output dir is gitignored.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------- #
# Paths                                                                    #
# ----------------------------------------------------------------------- #

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = DASHBOARD_DIR.parent
SKILLS_DIR = REPO_ROOT / "skills"
ANALYSIS_DIR = REPO_ROOT / "analysis"
FIGURES_DIR = REPO_ROOT / "figures"
OUT_DIR = DASHBOARD_DIR / "src" / "data" / "generated"
PUBLIC_FIGURES_DIR = DASHBOARD_DIR / "public" / "figures"

# ----------------------------------------------------------------------- #
# Helpers                                                                  #
# ----------------------------------------------------------------------- #


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ! WARN: invalid JSON {path.relative_to(REPO_ROOT)}: {e}",
              file=sys.stderr)
        return None


def read_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())


# ----------------------------------------------------------------------- #
# Skill classification                                                     #
# ----------------------------------------------------------------------- #

ADVERSARIAL_IDS = {"zz-adversarial-summarize-text"}
JUNK_IDS = {"-aug"}


def classify(skill_id: str) -> str:
    if skill_id in JUNK_IDS:
        return "junk"
    if skill_id.startswith("zz-mutation-"):
        return "mutation"
    if skill_id in ADVERSARIAL_IDS:
        return "adversarial"
    if skill_id.endswith("-aug"):
        return "augmented"
    return "production"


# Tranche-2 metadata (10 skills not in manifest.csv at submission time).
# All marked role="treatment" by default — review and override as needed.
TRANCHE_2: dict[str, dict[str, str]] = {
    "auth0-quickstart": {"owner": "auth0", "repo": "agent-skills",
                         "category": "auth", "role": "treatment"},
    "cloudformation": {"owner": "aws", "repo": "skills",
                       "category": "deploy", "role": "treatment"},
    "gha-security-review": {"owner": "github", "repo": "skills",
                            "category": "audit", "role": "treatment"},
    "pinecone-mcp": {"owner": "pinecone", "repo": "skills",
                     "category": "vector-db", "role": "treatment"},
    "prisma-postgres-setup": {"owner": "prisma", "repo": "skills",
                              "category": "database", "role": "treatment"},
    "prompt-images": {"owner": "replicate", "repo": "skills",
                      "category": "generation", "role": "treatment"},
    "semgrep": {"owner": "semgrep", "repo": "skills",
                "category": "audit", "role": "treatment"},
    "sentry-setup-ai-monitoring": {"owner": "sentry", "repo": "skills",
                                   "category": "observability",
                                   "role": "treatment"},
    "vercel-sandbox": {"owner": "vercel", "repo": "skills",
                       "category": "deploy", "role": "treatment"},
    "xcode-project-setup": {"owner": "apple", "repo": "skills",
                            "category": "mobile", "role": "treatment"},
}


def load_manifest() -> dict[str, dict[str, str]]:
    """Parse manifest.csv (tranche 1) and merge with hand-curated tranche 2."""
    manifest_path = REPO_ROOT / "manifest.csv"
    out: dict[str, dict[str, str]] = {}
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                out[row["id"]] = {
                    "owner": row.get("owner", "") or "",
                    "repo": row.get("repo", "") or "",
                    "category": row.get("category", "") or "uncategorised",
                    "role": row.get("role", "") or "treatment",
                }
    for skill_id, meta in TRANCHE_2.items():
        out.setdefault(skill_id, meta)
    return out


# ----------------------------------------------------------------------- #
# Cluster assignment — pinned to the report's bimodal stratification       #
# (Section 4 / 5.1). The bimodal cluster split is on paths_read F1, not    #
# hosts F1 (hosts F1 is undefined for ~half of n=25). Hardcoding the       #
# membership lists keeps the dashboard faithful to the published report.   #
# ----------------------------------------------------------------------- #

HIGH_F1_SKILLS = {
    "agent-browser", "frontend-design", "grill-me",
    "improve-codebase-architecture", "semgrep",
}
LOW_F1_SKILLS = {
    "auth0-quickstart", "cloudformation", "cookie-sync", "find-skills",
    "firebase-hosting-basics", "wrangler",
}


def assign_cluster(skill_id: str, f1: dict[str, float | None],
                   has_observed_network: bool) -> str:
    cls = classify(skill_id)
    if cls in ("augmented", "mutation", "adversarial"):
        return cls
    if skill_id in HIGH_F1_SKILLS:
        return "high-f1"
    if skill_id in LOW_F1_SKILLS:
        return "low-f1"
    if not has_observed_network:
        return "no-network"
    return "mid-f1"


# ----------------------------------------------------------------------- #
# Skill record extraction                                                  #
# ----------------------------------------------------------------------- #

def extract_skill(skill_dir: Path,
                  manifest: dict[str, dict[str, str]],
                  per_skill: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    skill_id = skill_dir.name
    if classify(skill_id) == "junk":
        return None

    pred_orig = read_json(skill_dir / "prediction.json")
    pred_fresh = read_json(skill_dir / "prediction-fresh.json")
    pred_codex = read_json(skill_dir / "prediction-codex.json")
    trace = read_json(skill_dir / "trace.json")
    policy = read_json(skill_dir / "skill-policy.json")
    task_md = read_text(skill_dir / "task.md")
    skill_md = read_text(skill_dir / "SKILL.md")

    if pred_orig is None and trace is None:
        # Skill dir missing both — likely incomplete or `-aug`-style stub
        return None

    meta = manifest.get(skill_id, {})
    cls = classify(skill_id)

    # Pull F1 from the canonical per-skill table where available
    per_skill_entry = per_skill.get(skill_id, {})
    fs_metrics = per_skill_entry.get("fs_metrics", {}) or {}
    net_metrics = per_skill_entry.get("net_metrics", {}) or {}

    f1: dict[str, float | None] = {
        "paths_read": (fs_metrics.get("paths_read") or {}).get("f1"),
        "paths_written": (fs_metrics.get("paths_written") or {}).get("f1"),
        "hosts": (net_metrics.get("hosts") or {}).get("f1"),
    }

    # Distinguish the two F1=None cases:
    #   - "match": both predicted and observed sets empty (true empty-vs-empty)
    #   - "miss":  predictor named patterns but none matched any observed item,
    #             or observed has items but predictor didn't cover any
    #   - "ok":    F1 defined, score normally
    #   - "no-data": axis metrics absent entirely (skill errored, etc.)
    def axis_status(axis_name: str, source: dict[str, Any]) -> str:
        m = source.get(axis_name)
        if not m:
            return "no-data"
        if m.get("f1") is not None:
            return "ok"
        n_obs = m.get("n_observed", 0) or 0
        n_pred = m.get("n_predicted", 0) or 0
        if n_obs == 0 and n_pred == 0:
            return "match"
        return "miss"

    f1_status: dict[str, str] = {
        "paths_read": axis_status("paths_read", fs_metrics),
        "paths_written": axis_status("paths_written", fs_metrics),
        "hosts": axis_status("hosts", net_metrics),
    }

    # Trace summary — count observed paths/hosts post-filter (the per-skill.json
    # table already reflects the agent-infra filter, so use those counts when
    # present; otherwise fall back to direct trace fields).
    observed = {
        "n_paths_read": (fs_metrics.get("paths_read") or {}).get("n_observed", 0),
        "n_paths_written": (fs_metrics.get("paths_written") or {}).get("n_observed", 0),
        "n_hosts": (net_metrics.get("hosts") or {}).get("n_observed", 0),
        "hosts": [],
    }
    if trace and isinstance(trace, dict):
        net = trace.get("net") or {}
        if isinstance(net, dict):
            obs_hosts = net.get("hosts_observed") or net.get("hosts") or []
            if isinstance(obs_hosts, list):
                observed["hosts"] = sorted({str(h) for h in obs_hosts})[:50]

    has_observed_network = bool(observed["n_hosts"]) or bool(observed["hosts"])
    cluster = assign_cluster(skill_id, f1, has_observed_network)

    pred_summary = {
        "n_paths_read": 0,
        "n_paths_written": 0,
        "n_hosts": 0,
        "n_subprocesses": 0,
        "hosts": [],
        "rationale": None,
    }
    if pred_orig and isinstance(pred_orig, dict):
        pred_summary["n_paths_read"] = len(pred_orig.get("paths_read") or [])
        pred_summary["n_paths_written"] = len(pred_orig.get("paths_written") or [])
        pred_summary["n_hosts"] = len(pred_orig.get("hosts") or [])
        pred_summary["n_subprocesses"] = len(pred_orig.get("subprocesses") or [])
        pred_summary["hosts"] = list(pred_orig.get("hosts") or [])[:30]
        pred_summary["rationale"] = pred_orig.get("rationale")

    return {
        "id": skill_id,
        "name": skill_id.replace("-", " ").replace("_", " ").title(),
        "owner": meta.get("owner") or None,
        "repo": meta.get("repo") or None,
        "category": meta.get("category") or "uncategorised",
        "role": meta.get("role") or "treatment",
        "class": cls,
        "cluster": cluster,
        "f1": f1,
        "f1_status": f1_status,
        "has_prediction": {
            "orig": pred_orig is not None,
            "fresh": pred_fresh is not None,
            "codex": pred_codex is not None,
        },
        "has_trace": {
            "orig": trace is not None,
            "codex": (skill_dir / "trace-codex.json").exists(),
            "realcreds": (skill_dir / "trace-realcreds.json").exists(),
            "multitask": any(
                (skill_dir / f"trace-l-{v}.json").exists()
                for v in ("alt1", "alt2")
            ),
            "stability": any(
                (skill_dir / f"trace-k-rep{i}.json").exists()
                for i in (1, 2)
            ),
            "effort": any(
                (skill_dir / f"trace-n-{v}.json").exists()
                for v in ("medium", "xhigh")
            ),
        },
        "has_policy": policy is not None,
        # Repo-relative path so the deployed dashboard JSON doesn't leak the
        # absolute build-time filesystem path.
        "skill_md_path": str((skill_dir / "SKILL.md").relative_to(REPO_ROOT).as_posix()) if skill_md else None,
        "skill_md_excerpt": (skill_md[:600] + "…") if skill_md and len(skill_md) > 600 else (skill_md or ""),
        "task_md": task_md or "",
        "prediction": pred_orig if isinstance(pred_orig, dict) else None,
        "prediction_fresh": pred_fresh if isinstance(pred_fresh, dict) else None,
        "prediction_codex": pred_codex if isinstance(pred_codex, dict) else None,
        "prediction_summary": pred_summary,
        "observed_summary": observed,
        "policy": policy if isinstance(policy, dict) else None,
        "f1_axes_full": {
            "paths_read": fs_metrics.get("paths_read"),
            "paths_written": fs_metrics.get("paths_written"),
            "paths_deleted": fs_metrics.get("paths_deleted"),
            "hosts": net_metrics.get("hosts"),
        },
    }


# ----------------------------------------------------------------------- #
# Findings — hand-curated catalogue derived from HANDOVER + report         #
# ----------------------------------------------------------------------- #

FINDINGS: list[dict[str, Any]] = [
    {
        "id": "A",
        "slug": "agentic-not-architectural-blind-spots",
        "title": "Blind spots are agentic, not architectural",
        "one_line": "Both Claude Code and Codex CLI skip SKILL.md’s retrieval directives — pre-training already contains the answer.",
        "section": "5.2",
        "layer": ["methodology"],
        "pattern": "agent-runtime-opacity",
        "severity": "info",
        "key_numbers": [
            {"label": "Cross-agent confirmation",
             "value": "Codex also did not hit developers.cloudflare.com"},
        ],
        "related_skills": ["wrangler"],
        "body_md": (
            "Initial framing: agent-tool-mediated IO (WebSearch, WebFetch, "
            "subagent dispatch) is invisible to syscall instrumentation. "
            "Cross-agent control under Codex CLI eliminated this as the "
            "explanation — Codex shells out to raw curl/wget, yet still "
            "elected pre-training over retrieval on the wrangler task. "
            "**SKILL.md retrieval mandates are aspirational, not predictive of "
            "runtime IO.**"
        ),
    },
    {
        "id": "B",
        "slug": "live-loading-skills",
        "title": "Live-loading skills break the prediction contract",
        "one_line": "SKILL.md-only prediction is structurally insufficient for skills that load behaviour at runtime.",
        "section": "5.2",
        "layer": ["methodology", "L2-llm"],
        "pattern": "agent-runtime-opacity",
        "severity": "info",
        "key_numbers": [],
        "related_skills": ["agent-browser", "find-skills"],
        "body_md": (
            "Skills like agent-browser or find-skills load tool capabilities "
            "or sub-skills at runtime — the SKILL.md text is a partial "
            "specification. Static prediction systematically under-covers "
            "this class. Live loading is a structural blind spot that "
            "requires either runtime instrumentation (this audit) or "
            "manifest-based registration (a forward path)."
        ),
    },
    {
        "id": "C",
        "slug": "cli-wrapping-network-underdeclaration",
        "title": "CLI-wrapping skills under-declare network footprint",
        "one_line": "Every CLI-wrapping skill in the sample emits at least one undeclared host.",
        "section": "5.1",
        "layer": ["L2-llm", "policy-design"],
        "pattern": "vendor-cli-underdeclaration",
        "severity": "high",
        "key_numbers": [
            {"label": "Hosts F1 mean (25 prod. skills, n=6)", "value": "0.431"},
            {"label": "Hosts F1 mean (n=9 incl. 3 Finding L aug variants)", "value": "0.475 [0.399, 0.542]"},
            {"label": "Bimodal split (CLI-wrapper vs pure-text)",
             "value": "Mann-Whitney p=0.030"},
        ],
        "related_skills": ["wrangler", "firebase-hosting-basics", "find-skills",
                           "firecrawl-scrape", "web-search", "azure-validate",
                           "cloudformation", "auth0-quickstart"],
        "body_md": (
            "The headline empirical claim. SKILL.md text systematically "
            "under-enumerates network hosts for skills that wrap a vendor "
            "CLI. Confirmed across at least 8 skills in the n=25 sample. "
            "The LLM predictor reading SKILL.md alone systematically "
            "under-predicts; the trace shows the hosts; the gap *is* the "
            "data."
        ),
    },
    {
        "id": "D",
        "slug": "setup-prerequisites-inflate-trace",
        "title": "Setup prerequisites inflate trace if not pre-installed",
        "one_line": "Methodological — pre-install per-skill CLIs to keep trace focused on task IO.",
        "section": "methodology",
        "layer": ["methodology"],
        "pattern": "methodology",
        "severity": "info",
        "key_numbers": [],
        "related_skills": [],
        "body_md": (
            "Skills that bootstrap their CLI tooling on first invocation "
            "contaminate the trace with package-install IO. "
            "harness/setup-skills.sh pre-installs all CLIs (wrangler, "
            "firebase-tools, semgrep, prisma, vercel, replicate-py, awscli) "
            "so the trace reflects task work, not bootstrap."
        ),
    },
    {
        "id": "E",
        "slug": "undocumented-bundled-siblings",
        "title": "Undocumented bundled siblings",
        "one_line": "improve-codebase-architecture/DEEPENING.md is referenced from SKILL.md but ships separately.",
        "section": "mentioned",
        "layer": ["L2-llm"],
        "pattern": "vendor-cli-underdeclaration",
        "severity": "low",
        "key_numbers": [],
        "related_skills": ["improve-codebase-architecture"],
        "body_md": (
            "Bundled-sibling files (referenced markdown that ships in the "
            "skill bundle but is not the canonical SKILL.md) are a "
            "predictor blind spot. The predictor reads SKILL.md alone per "
            "methodology §6, so any malice or undeclared IO living in "
            "siblings escapes static review. Closes only by ingesting "
            "bundled siblings as part of the prediction context (Mutation "
            "M4 closure path)."
        ),
    },
    {
        "id": "F",
        "slug": "xhigh-effort-helps-on-long-skills",
        "title": "xhigh predictor catches more than default",
        "one_line": "On long, referential SKILL.mds, --effort xhigh extracts more declared IO than --effort default.",
        "section": "methodology",
        "layer": ["methodology", "L2-llm"],
        "pattern": "methodology",
        "severity": "info",
        "key_numbers": [],
        "related_skills": [],
        "body_md": (
            "Comparing default-effort vs xhigh-effort prediction on the "
            "same SKILL.md text shows xhigh extracts a larger candidate "
            "set, particularly on referential SKILL.mds with many @-link "
            "or relative-path references. Methodology lock chose xhigh as "
            "the canonical predictor effort."
        ),
    },
    {
        "id": "G",
        "slug": "unconditional-vendor-telemetry",
        "title": "Unconditional vendor telemetry beacons",
        "one_line": "wrangler→sparrow.cloudflare.com, semgrep→metrics.semgrep.dev, firebase→firebase-public.firebaseio.com.",
        "section": "5.1",
        "layer": ["L2-llm", "policy-design"],
        "pattern": "vendor-cli-underdeclaration",
        "severity": "high",
        "key_numbers": [
            {"label": "Telemetry hosts identified",
             "value": "≥4 across n=25 (sharper formulation of Finding C)"},
        ],
        "related_skills": ["wrangler", "semgrep", "firebase-hosting-basics",
                           "find-skills"],
        "body_md": (
            "The most consistent failure mode within Finding C is "
            "unconditional vendor telemetry. wrangler invocations (any "
            "subcommand, including --dry-run) emit a beacon to "
            "sparrow.cloudflare.com not named anywhere in SKILL.md. semgrep "
            "scan invocations emit metrics.semgrep.dev. firebase-tools "
            "contacts firebase-public.firebaseio.com on startup. find-skills "
            "contacts the installer service add-skill.vercel.sh. These are "
            "vendor-side unconditional probes — the cross-agent test "
            "(Codex) confirms they are not Claude-Code-specific. **Direct "
            "policy implication**: any SKILL.md-derived sandbox policy "
            "will mis-classify these beacons unless either (a) a global "
            "telemetry-suffix deny-overlay is added, or (b) the LLM "
            "extraction is post-processed to expand wildcards into "
            "explicit subdomain enumerations."
        ),
    },
    {
        "id": "H",
        "slug": "cross-agent-footprint-inflation",
        "title": "Cross-agent syscall-trace inflation is bootstrap-cost",
        "one_line": "Codex 256× more writes than Claude on wrangler — but ~99% is plugin-marketplace metadata, not task work.",
        "section": "5.3",
        "layer": ["methodology"],
        "pattern": "agent-runtime-opacity",
        "severity": "medium",
        "key_numbers": [
            {"label": "Apparent ratio", "value": "256× (Codex 2556 / Claude 10)"},
            {"label": "Task-attributable ratio after baseline subtraction",
             "value": "1:1 (9 vs 10)"},
        ],
        "related_skills": ["wrangler"],
        "body_md": (
            "A clean per-(skill, agent) policy-derivation comparison "
            "requires per-agent baseline subtraction. Without it, naive "
            "trace-based agent comparisons measure agent identity, not "
            "task behaviour. Of Codex's 2556 writes, 2541 were "
            "plugin-marketplace metadata (117 vendors × N files) "
            "tempfs-extracted at startup; 104 were ~/.codex/ agent-state. "
            "After filtering, task-attributable writes drop to 9. Useful "
            "methodology lesson for any work in this direction."
        ),
    },
    {
        "id": "I",
        "slug": "static-prediction-surfaces-malice",
        "title": "Structured static prediction surfaces malicious intent honestly",
        "one_line": "The predictor lists attacker.example.com in its hosts field rather than refusing to engage.",
        "section": "5.4",
        "layer": ["L2-llm"],
        "pattern": "adversarial-maintainer",
        "severity": "high",
        "key_numbers": [],
        "related_skills": ["zz-adversarial-summarize-text"],
        "body_md": (
            "On the synthetic adversarial demo (zz-adversarial-summarize-"
            "text/), the xhigh-effort predictor extracted the malicious "
            "intent honestly — it listed attacker.example.com in the hosts "
            "field and labelled the rationale 'prompt-injection/adversarial "
            "skill'. Good news for hardening tooling: a "
            "structured-extraction prediction layer is a usable static-"
            "analysis red flag *because* it doesn't downplay malicious "
            "instructions."
        ),
    },
    {
        "id": "J",
        "slug": "defense-in-depth-empirically-validated",
        "title": "Defense-in-depth empirically validated",
        "one_line": "All 6 mutations × 4 layers: every attack contained by at least one layer.",
        "section": "5.4",
        "layer": ["L1-static", "L2-llm", "L3-runtime-claude", "L4-runtime-codex"],
        "pattern": "adversarial-maintainer",
        "severity": "high",
        "key_numbers": [
            {"label": "Per-layer detection",
             "value": "L1 83% / L2 67% / L3 100% / L4 100%"},
            {"label": "Coverage", "value": "6/6 attacks contained"},
            {"label": "L1 under realistic minimal regex",
             "value": "drops to 0/6"},
        ],
        "related_skills": [
            "zz-mutation-1-obfuscated-curl", "zz-mutation-2-dns-exfil",
            "zz-mutation-3-webfetch-indirection", "zz-mutation-4-bundled-sibling",
            "zz-mutation-5-time-bombed", "zz-mutation-6-dependency-confusion",
        ],
        "body_md": (
            "The 6×4 mutation suite empirically validates Professor Monperrus's "
            "topic-26 framing: static analysis is necessary-but-insufficient. "
            "L1 misses M3 (prose-only WebFetch indirection). L2 misses M4 "
            "(bundled-sibling reference) and M6 (dependency-confusion via "
            "deceptive package naming). L3 + L4 catch everything. The "
            "ablation drops L1 to 0/6 under a realistic three-rule regime "
            "(sudo, rm -rf /, pipe-to-shell), confirming brittleness."
        ),
    },
    {
        "id": "K",
        "slug": "refusal-verbosity-differs",
        "title": "Refusal verbosity differs across aligned agents",
        "one_line": "Claude Code warns the user; Codex silently refuses without operator-visible signal.",
        "section": "5.4",
        "layer": ["L3-runtime-claude", "L4-runtime-codex"],
        "pattern": "agent-runtime-opacity",
        "severity": "medium",
        "key_numbers": [],
        "related_skills": ["zz-adversarial-summarize-text"],
        "body_md": (
            "Claude Code's user-facing warning is operationally valuable — "
            "the user installing a compromised skill receives an immediate "
            "alert. Codex's silent compliance is technically correct but "
            "provides no signal. Tooling that derives policy from agent "
            "traces should also surface the model's own refusal-rationales "
            "as a signal channel, since the verbose channel is a free "
            "byproduct under one agent and absent under another."
        ),
    },
    {
        "id": "L",
        "slug": "augmented-skillmd-closes-gap",
        "title": "Augmented SKILL.md closes the gap on thin priors",
        "one_line": "+25pp hosts F1 on firebase-hosting-basics from a single 'Observed Runtime Endpoints' section.",
        "section": "5.6",
        "layer": ["L2-llm", "policy-design"],
        "pattern": "vendor-cli-underdeclaration",
        "severity": "info",
        "key_numbers": [
            {"label": "firebase-hosting-basics hosts F1",
             "value": "0.364 → 0.615 (+25pp)"},
            {"label": "wrangler / semgrep lift",
             "value": "minimal (priors already capped out)"},
        ],
        "related_skills": ["firebase-hosting-basics-aug", "wrangler-aug",
                           "semgrep-aug"],
        "body_md": (
            "Three augmented SKILL.md variants tested: thin priors (firebase-"
            "hosting-basics, 46-line conceptual prose) saw the largest "
            "single F1 lift in the experiment. wrangler and semgrep showed "
            "minimal lift because their original predictors had already "
            "inferred most of the missing hosts from CLI-vendor convention "
            "or wildcard predicates. **Most actionable single recommendation**: "
            "add an 'Observed Runtime Endpoints' section to thin SKILL.mds. "
            "Cheap to author, immediately closes the bottom of the F1 "
            "distribution."
        ),
    },
    {
        "id": "M",
        "slug": "wildcards-sabotage-policy-discrimination",
        "title": "Wildcard predictions sabotage policy discrimination",
        "one_line": "*.cloudflare.com accidentally admits sparrow.cloudflare.com — wildcards must be deflated.",
        "section": "6",
        "layer": ["L2-llm", "policy-design"],
        "pattern": "vendor-cli-underdeclaration",
        "severity": "high",
        "key_numbers": [],
        "related_skills": ["wrangler"],
        "body_md": (
            "The predictor's *.cloudflare.com is technically a correct "
            "summary of declared CLI hosts, but in deployment it admits "
            "the telemetry sub-domain sparrow.cloudflare.com. Post-process "
            "the prediction to either (a) expand wildcards into explicit "
            "subdomain enumerations, or (b) pair every wildcard predicate "
            "with a global telemetry-suffix deny-overlay. **This is the "
            "first of three composition requirements** that turn the "
            "LLM-extracted allowlist into a deployable capability artefact."
        ),
    },
    {
        "id": "N",
        "slug": "predictor-variance-llm-dominant",
        "title": "Predictor variance: LLM choice dominates context choice",
        "one_line": "Cross-LLM Jaccard 0.41 on hosts; cross-context Jaccard 0.72.",
        "section": "5.5",
        "layer": ["methodology", "L2-llm"],
        "pattern": "methodology",
        "severity": "medium",
        "key_numbers": [
            {"label": "orig × fresh-Claude hosts Jaccard", "value": "0.723"},
            {"label": "orig × Codex hosts Jaccard", "value": "0.431"},
            {"label": "fresh × Codex hosts Jaccard", "value": "0.410"},
        ],
        "related_skills": [],
        "body_md": (
            "Two methodological conclusions. First, context contamination "
            "is real but moderate (clean-Claude vs context-Claude Jaccard "
            "0.58–0.80). Second, cross-LLM variance dominates context "
            "variance at every axis. **Implication**: the headline F1 "
            "numbers are Claude Opus 4.7-specific. The bimodal pattern "
            "itself is robust across predictors; absolute magnitudes are "
            "not. Any production deployment must fix predictor identity + "
            "effort up front."
        ),
    },
    {
        "id": "O",
        "slug": "structured-extraction-inherits-malice",
        "title": "Structured-extraction policy generators inherit maintainer-supplied malice",
        "one_line": "All 3 predictor sources emit attacker.example.com verbatim in the structured hosts field.",
        "section": "5.7",
        "layer": ["L2-llm", "policy-design"],
        "pattern": "adversarial-maintainer",
        "severity": "high",
        "key_numbers": [
            {"label": "Predictor sources", "value": "3/3 (orig, fresh, codex)"},
        ],
        "related_skills": ["zz-adversarial-summarize-text"],
        "body_md": (
            "Late-add finding (Phase 1.A). Structured-extraction policy "
            "generators are *safety-blind by construction*; they faithfully "
            "encode whatever the SKILL.md names, including attacker hosts. "
            "Pair the SKILL.md-derived allowlist with a separate trust "
            "check before deployment — this is the **maintainer-reputation "
            "gate**, the second of three composition requirements. "
            "Defense-in-depth is necessary, not optional."
        ),
    },
]

# ----------------------------------------------------------------------- #
# Aggregates extracted from analysis/                                      #
# ----------------------------------------------------------------------- #

def build_aggregates() -> dict[str, Any]:
    summary = read_json(ANALYSIS_DIR / "summary.json") or {}
    stats = read_json(ANALYSIS_DIR / "stats.json") or {}
    policy_eval = read_json(ANALYSIS_DIR / "policy-eval.json") or {}
    static_per_skill = read_json(ANALYSIS_DIR / "static-per-skill.json") or []

    return {
        "summary": summary,
        "stats": stats,
        "policy_eval": policy_eval,
        "static_per_skill_count": len(static_per_skill) if isinstance(static_per_skill, list) else len(static_per_skill or {}),
        "headline": [
            {"label": "Hosts F1 (mean, 25 prod. skills)",
             "value": "0.431",
             "ci": "n=6 with defined F1",
             "note": "Aug-inclusive value (n=9 incl. 3 Finding L variants): 0.475 [0.399, 0.542]"},
            {"label": "LLM vs static recall",
             "value": "2.50×",
             "ci": "Wilcoxon p=0.047, McNemar p=0.003 (n=11 incl. aug)",
             "note": "Production-only McNemar p≈0.125 (not sig. at α=0.05); recall gap directionally consistent"},
            {"label": "Mutation containment",
             "value": "6/6",
             "ci": "L1 83% · L2 67% · L3 100% · L4 100%",
             "note": "L1 → 0/6 under realistic minimal regex"},
            {"label": "Policy enforcement: legit-allow",
             "value": "77%",
             "ci": "n=8 skills with non-empty network surface",
             "note": "telemetry-catch 50%"},
            {"label": "Cross-LLM Jaccard (hosts)",
             "value": "0.41",
             "ci": "Claude vs Codex on n=25",
             "note": "context-only Jaccard 0.72"},
            {"label": "Bimodal split",
             "value": "Mann-Whitney p=0.030",
             "ci": "paths_read F1, U=6",
             "note": "CLI-wrapper vs pure-text"},
        ],
        "n_production": 25,
        "n_mutations": 6,
        "n_augmented": 3,
        "n_adversarial": 1,
    }


# ----------------------------------------------------------------------- #
# Analysis docs — narrative pages                                          #
# ----------------------------------------------------------------------- #

ANALYSIS_DOCS = [
    ("stats", "Statistical rigor — bootstrap CIs, McNemar's, Wilcoxon"),
    ("static-vs-dynamic", "Static regex baseline vs LLM predictor"),
    ("policy-eval", "Retroactive policy-allowlist evaluation"),
    ("policy-enforcement", "Enforcement simulation + iptables-in-netns recipe"),
    ("policy-bundle-prototype", "Registry-deployable policy bundle prototype"),
    ("mutation-suite", "6×4 detection-rate table (mutation × defense layer)"),
    ("mutation-suite-ablation", "Brittleness ablation across regex regimes"),
    ("failure-mode-taxonomy", "24 hosts × 7 categories failure-mode taxonomy"),
    ("predictor-variance", "Pairwise Jaccard between orig/fresh/Codex predictors"),
    ("predictor-vs-truth", "F1 per predictor source against same observed traces"),
    ("subgroup-analysis", "Mann-Whitney + Kruskal-Wallis across stratifications"),
    ("stability-effort", "Repeat-invocation stability + effort sensitivity"),
    ("multitask-fuzzing", "Alternate-prompt sensitivity (Phase 3.L)"),
    ("mechanism-investigation", "Why findings happened — 256× decomposition"),
    ("finding-o-adversarial-policy", "Finding O analysis"),
    ("citation-justifications", "Per-citation credibility + verification record"),
    ("sandboxing-granularity", "G1/G2/G3/G4 granularity comparison"),
]


def build_analysis_docs() -> list[dict[str, Any]]:
    out = []
    for slug, title in ANALYSIS_DOCS:
        md_path = ANALYSIS_DIR / f"{slug}.md"
        json_path = ANALYSIS_DIR / f"{slug}.json"
        body = read_text(md_path) or ""
        json_excerpt = read_json(json_path)
        if not body:
            continue
        out.append({
            "slug": slug,
            "title": title,
            "body_md": body,
            "json_excerpt": json_excerpt,
        })
    return out


# ----------------------------------------------------------------------- #
# Mutation suite                                                           #
# ----------------------------------------------------------------------- #

def build_mutation_suite() -> dict[str, Any]:
    raw = read_json(ANALYSIS_DIR / "mutation-suite.json") or {}
    ablation = read_json(ANALYSIS_DIR / "mutation-suite-ablation.json") or {}
    return {
        "per_mutation": raw.get("per_mutation", []),
        "per_layer_rates": raw.get("per_layer_rates", {}),
        "coverage": raw.get("coverage", {}),
        "ablation": ablation,
    }


# ----------------------------------------------------------------------- #
# Policy bundles                                                           #
# ----------------------------------------------------------------------- #

def build_policy() -> dict[str, Any]:
    bundles = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        policy_file = skill_dir / "skill-policy.json"
        if policy_file.exists():
            data = read_json(policy_file)
            if data:
                bundles.append({"skill_id": skill_dir.name, "bundle": data})
    eval_data = read_json(ANALYSIS_DIR / "policy-eval.json") or {}
    enforcement = read_json(ANALYSIS_DIR / "policy-enforcement.json") or {}
    return {
        "bundles": bundles,
        "eval": eval_data,
        "enforcement": enforcement,
    }


# ----------------------------------------------------------------------- #
# Figures                                                                  #
# ----------------------------------------------------------------------- #

FIGURE_CAPTIONS = {
    "fig-01-f1-distribution": (
        "F1 distribution per skill across the three IO axes (paths_read, "
        "paths_written, hosts). Bimodal pattern is visible on the paths_read "
        "axis: CLI-wrappers cluster low, pure-text/single-output skills "
        "cluster high. Mann-Whitney p=0.030."
    ),
    "fig-02-predictor-variance": (
        "Pairwise Jaccard between orig-Claude / fresh-Claude / Codex "
        "predictors across all four IO axes. Cross-LLM variance "
        "dominates cross-context variance at every axis (Finding N)."
    ),
    "fig-03-pred-vs-obs": (
        "Predicted set size vs observed set size, per skill, per axis. "
        "Diagonal line = perfect calibration. Below-diagonal = "
        "under-prediction (the headline gap)."
    ),
    "fig-04-ci-forest": (
        "Bootstrap 95% CI forest plot per IO axis. Hosts F1 = 0.431 "
        "(25 production skills, n=6) / 0.475 [0.399, 0.542] (n=9 incl. aug). "
        "Single-predictor variance is captured; "
        "cross-predictor variance is reported separately in Section 5.5."
    ),
    "fig-05-failure-modes": (
        "Failure-mode taxonomy: 24 host-misses × 7 categories. "
        "Telemetry-beacon and binary-fetch-CDN dominate the undeclared "
        "tier. Each category maps to a distinct enforcement granularity "
        "(suffix-deny, SHA-pinned, credential-scoped)."
    ),
    "fig-06-mutation-suite": (
        "6×4 mutation × defense-layer detection-rate table. Defense-"
        "in-depth coverage 6/6. L1 misses M3 (prose-only); L2 misses "
        "M4 (bundled sibling) and M6 (dependency confusion). Ablation "
        "drops L1 from 83% → 0% under realistic regex."
    ),
}


def build_figures() -> list[dict[str, str]]:
    figures = []
    for slug, caption in FIGURE_CAPTIONS.items():
        svg = FIGURES_DIR / f"{slug}.svg"
        png = FIGURES_DIR / f"{slug}.png"
        if not svg.exists():
            continue
        # copy to public/ so Astro serves them
        copy_file(svg, PUBLIC_FIGURES_DIR / f"{slug}.svg")
        if png.exists():
            copy_file(png, PUBLIC_FIGURES_DIR / f"{slug}.png")
        figures.append({
            "slug": slug,
            "title": slug.replace("fig-", "Figure ").replace("-", " ").title(),
            "caption": caption,
            "svg": f"/figures/{slug}.svg",
            "png": f"/figures/{slug}.png" if png.exists() else None,
        })
    return figures


# ----------------------------------------------------------------------- #
# Report excerpts                                                          #
# ----------------------------------------------------------------------- #

def build_report_excerpts() -> dict[str, str]:
    text = read_text(REPO_ROOT / "report.md") or ""
    out: dict[str, str] = {}

    # Abstract — between "## Abstract" and "## 1. Task and approach"
    m = re.search(r"## Abstract\s+(.*?)\n## 1\.", text, re.DOTALL)
    if m:
        out["abstract"] = m.group(1).strip()

    # Threat model section (2.2)
    m = re.search(r"### 2\.2 Threat model\s+(.*?)\n##", text, re.DOTALL)
    if m:
        out["threat_model"] = m.group(1).strip()

    # Section 6 (constructive answer)
    m = re.search(r"## 6\. (.*?)\n## 7\.", text, re.DOTALL)
    if m:
        out["constructive_answer"] = m.group(1).strip()

    # Section 8 (reflection)
    m = re.search(r"## 8\. (.*?)\n## 9\.", text, re.DOTALL)
    if m:
        out["reflection"] = m.group(1).strip()

    # Executive summary 1-paragraph
    exec_text = read_text(REPO_ROOT / "EXECUTIVE_SUMMARY.md") or ""
    m = re.search(r"## In one paragraph\s+(.*?)\n##", exec_text, re.DOTALL)
    if m:
        out["one_paragraph"] = m.group(1).strip()

    return out


# ----------------------------------------------------------------------- #
# Main                                                                     #
# ----------------------------------------------------------------------- #

def main() -> int:
    print(f"build-data.py — emitting to {OUT_DIR.relative_to(DASHBOARD_DIR)}")

    manifest = load_manifest()
    per_skill_list = read_json(ANALYSIS_DIR / "per-skill.json") or []
    per_skill = {entry.get("skill_id", ""): entry for entry in per_skill_list}

    skills: list[dict[str, Any]] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        rec = extract_skill(skill_dir, manifest, per_skill)
        if rec:
            skills.append(rec)
    print(f"  skills: {len(skills)} ("
          f"production={sum(1 for s in skills if s['class']=='production')}, "
          f"augmented={sum(1 for s in skills if s['class']=='augmented')}, "
          f"mutations={sum(1 for s in skills if s['class']=='mutation')}, "
          f"adversarial={sum(1 for s in skills if s['class']=='adversarial')})")

    write_json(OUT_DIR / "skills.json", skills)
    write_json(OUT_DIR / "findings.json", FINDINGS)
    write_json(OUT_DIR / "analysis.json", build_analysis_docs())
    write_json(OUT_DIR / "aggregates.json", build_aggregates())
    write_json(OUT_DIR / "mutation-suite.json", build_mutation_suite())
    write_json(OUT_DIR / "policy.json", build_policy())
    write_json(OUT_DIR / "figures.json", build_figures())
    write_json(OUT_DIR / "report-excerpts.json", build_report_excerpts())

    print("  ✓ done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
