#!/usr/bin/env python3
"""Phase 4.7+ — Registry-level policy-bundle prototype.

Concrete demonstration that the SKILL.md → policy direction can ship as a
deployable artefact alongside the SKILL.md itself, in the same way SLSA-attested
provenance ships alongside an npm package.

For a target skill, this script generates a `skill-policy.json` companion file
that an installer (skills.sh, Socket, or the agent-runtime itself) could read
to enforce per-skill capability scoping at install time. The bundle composes:

  1. SKILL.md-derived per-skill allowlist (from prediction.json hosts)
  2. Wildcard-deflation pass (Finding M) — expand `*.X` predicates into the
     specific subdomains observed in the trace, plus a residual `*.X` entry
     marked as "subdomain-bounded" so a runtime can decide whether to honour it
  3. Telemetry-suffix deny-overlay — global blocklist that wins over allowlist
     wildcards; addresses Finding M's wildcard-sabotage failure mode
  4. Maintainer-trust hint — derived from the SKILL.md frontmatter (org-owned
     if maintainer matches a known-vendor list; otherwise long-tail)
  5. Augmentation suggestion — for skills where Finding L showed augmentation
     would close >5pp of F1 gap, ship the suggested append-text

Output: skills/<id>/skill-policy.json, plus a registry-style aggregate at
       analysis/policy-bundle-firebase-hosting-basics-aug.json (the demo target)
       and a markdown writeup at analysis/policy-bundle-prototype.md
"""
from __future__ import annotations
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Known telemetry suffixes (Finding M deny-overlay). In production this would
# come from a maintained threat-intel feed.
TELEMETRY_SUFFIX_DENY = [
    "sparrow.cloudflare.com",
    "metrics.semgrep.dev",
    "ogads-pa.clients6.google.com",
    "metrics.*.dev",
    "analytics.*",
    "telemetry.*",
    "*-telemetry.*.com",
]

# Vendor-trust list — first-class corporate-vendor maintainers.
TRUSTED_MAKERS = {
    "anthropics", "anthropic", "cloudflare", "firebase", "vercel-labs",
    "microsoft", "google", "auth0", "getsentry", "semgrep", "prisma",
    "pinecone-io", "replicate", "browserbase", "firecrawl", "openai",
}


def deflate_wildcards(allowlist: list[str], observed_hosts: list[str]) -> dict:
    """Expand wildcard predicates against the actual observed-host set so the
    deployed allowlist is as specific as possible. Returns a dict with
    structured entries plus the residual wildcard for runtime-deciding."""
    deflated = []
    residual_wildcards = []
    for pred in allowlist:
        if pred.startswith("*."):
            suffix = pred[2:]
            specific_subdomains = sorted({
                h.lower() for h in observed_hosts
                if h.lower().endswith("." + suffix) or h.lower() == suffix
            })
            if specific_subdomains:
                for sub in specific_subdomains:
                    deflated.append({"host": sub, "predicate": pred,
                                     "source": "wildcard-deflated", "type": "exact"})
                residual_wildcards.append({"host_pattern": pred,
                                           "subdomain_bounded_to": specific_subdomains,
                                           "type": "wildcard-bounded"})
            else:
                residual_wildcards.append({"host_pattern": pred,
                                           "subdomain_bounded_to": None,
                                           "type": "wildcard-unconstrained",
                                           "note": "no observed subdomain matches; runtime should reject by default"})
        else:
            deflated.append({"host": pred, "source": "literal", "type": "exact"})
    return {"explicit_subdomains": deflated, "residual_wildcards": residual_wildcards}


def maker_trust_hint(skill_dir: Path) -> dict:
    """Read SKILL.md frontmatter (or fall back to manifest) to extract the
    maintainer org. Return a structured trust hint."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"maintainer": None, "trust_tier": "unknown"}
    text = skill_md.read_text()
    # Try to extract from frontmatter or use directory name as a fallback.
    # We don't parse YAML front-matter here; a real implementation would.
    sid = skill_dir.name
    # Look up against TRUSTED_MAKERS using the skill_id as a heuristic.
    trust_tier = "long-tail"
    matched = None
    for trusted in TRUSTED_MAKERS:
        if trusted in sid.lower():
            trust_tier = "first-class-vendor"
            matched = trusted
            break
    return {"maintainer_signal_from_skill_id": matched,
            "trust_tier": trust_tier,
            "note": ("In a deployed registry, maintainer identity should come "
                     "from a separate signed assertion — Sigstore for OSS skills, "
                     "an attestation chain for enterprise skills.")}


def augmentation_suggestion(orig_dir: Path, aug_dir: Path) -> dict | None:
    """If an *-aug variant exists, surface the augmentation diff as a suggestion."""
    if not aug_dir.exists():
        return None
    aug_md = aug_dir / "SKILL.md"
    orig_md = orig_dir / "SKILL.md"
    if not (aug_md.exists() and orig_md.exists()):
        return None
    aug_text = aug_md.read_text()
    orig_text = orig_md.read_text()
    if len(aug_text) <= len(orig_text):
        return None
    # The augmentation is the suffix.
    addendum = aug_text[len(orig_text):].strip()
    return {
        "available": True,
        "addendum_preview": addendum[:600],
        "addendum_length_chars": len(addendum),
        "note": ("Append this to SKILL.md to lift hosts F1 (Finding L). "
                 "Empirical lift on this skill is in analysis/per-skill.json's "
                 "*-aug entry."),
    }


def generate_bundle(skill_id: str) -> dict:
    sd = PROJECT_ROOT / "skills" / skill_id
    aug_sd = PROJECT_ROOT / "skills" / f"{skill_id}-aug"

    pred_path = sd / "prediction.json"
    trace_path = sd / "trace.json"
    if not pred_path.exists():
        return {"skill_id": skill_id, "error": "no prediction.json"}

    pred = json.loads(pred_path.read_text())
    trace = json.loads(trace_path.read_text()) if trace_path.exists() else {}
    observed_hosts = trace.get("net", {}).get("dns_queries", [])

    # Per-skill capability set
    network_egress = deflate_wildcards(pred.get("hosts", []), observed_hosts)
    fs_reads = pred.get("paths_read", [])
    fs_writes = pred.get("paths_written", [])
    subprocs = pred.get("subprocesses", [])

    bundle = {
        "skill_policy_schema_version": "0.1-prototype",
        "generated_for_skill_id": skill_id,
        "generation_method": "Claude Opus 4.7 xhigh-effort SKILL.md-only prediction (predict.py) + wildcard deflation (Finding M post-process)",
        "capability_declarations": {
            "network_egress": {
                "explicit_allow": network_egress["explicit_subdomains"],
                "wildcard_residuals": network_egress["residual_wildcards"],
                "telemetry_deny_overlay": TELEMETRY_SUFFIX_DENY,
                "policy_decision_rule": (
                    "deny-overlay wins over allowlist wildcards; "
                    "explicit_allow entries are admitted unconditionally; "
                    "wildcard_residuals are subject to runtime configuration "
                    "(default: reject if subdomain_bounded_to is null, else "
                    "admit only the listed subdomains)."
                ),
            },
            "filesystem_read": {
                "predicates": fs_reads,
                "scope": "workdir-relative + ~/.config/<vendor>/* per Finding D",
            },
            "filesystem_write": {
                "predicates": fs_writes,
                "scope": "workdir-relative; reject everything outside",
            },
            "subprocess_spawn": {
                "binaries": subprocs,
                "scope": "execve allowlist; reject other binaries",
            },
            "agent_tool_invocation": {
                "note": "Read from SKILL.md frontmatter `allowed-tools` if declared; otherwise the agent-runtime base policy applies.",
                "example_existing_skills_with_declared_allowed_tools": ["gha-security-review"],
            },
        },
        "maintainer_trust_hint": maker_trust_hint(sd),
        "augmentation_suggestion": augmentation_suggestion(sd, aug_sd) or {"available": False},
        "headline_metrics_for_this_skill": {
            "predicted_hosts_count": len(pred.get("hosts", [])),
            "observed_skill_attributable_hosts": [
                h for h in observed_hosts
                if h not in {"api.anthropic.com", "downloads.claude.ai",
                             "mcp-proxy.anthropic.com", "http-intake.logs.us5.datadoghq.com",
                             "chatgpt.com", "ab.chatgpt.com", "ipv4only.arpa", "localhost"}
            ],
        },
        "compliance_with_topic_26_subgoals": {
            "capability_based_permission_model": "yes (this bundle is the policy artefact)",
            "sandboxing_granularity_supported": "per-skill (this bundle); per-tool-call by composing with SKILL.md `allowed-tools`",
            "static_plus_semantic_detection": "yes (LLM-extracted prediction is the static + semantic step; runtime alignment is the L3 enforcement layer)",
        },
        "non_authoritative_disclaimer": (
            "This bundle is generated automatically and is not a substitute for "
            "the maintainer-published SKILL.md. It is intended to be installed "
            "alongside the SKILL.md, not in place of it. The policy decision rule "
            "above is the runtime contract; deployers should implement the deny-"
            "overlay precedence rule explicitly."
        ),
    }
    return bundle


def main():
    # Demo target: firebase-hosting-basics-aug (Finding L's biggest lift)
    targets = ["firebase-hosting-basics-aug", "wrangler", "semgrep",
               "firecrawl-scrape", "auth0-quickstart"]

    bundles = {}
    for sid in targets:
        bundle = generate_bundle(sid)
        bundles[sid] = bundle
        out_path = PROJECT_ROOT / "skills" / sid / "skill-policy.json"
        if "error" not in bundle:
            out_path.write_text(json.dumps(bundle, indent=2))
            print(f"=> {out_path}")
        else:
            print(f"  skip {sid}: {bundle['error']}")

    # Aggregate writeup
    out_md = PROJECT_ROOT / "analysis" / "policy-bundle-prototype.md"
    lines = [
        "# Phase 4.7+ — Registry-Level Policy-Bundle Prototype",
        "",
        "Concrete demonstration that the SKILL.md → policy direction can ship as a",
        "deployable artefact alongside the SKILL.md itself. For each target skill,",
        "the prototype generates a `skill-policy.json` companion file with five",
        "components:",
        "",
        "1. **Capability declarations** — network egress (with wildcard deflation per Finding M), filesystem read/write predicates, subprocess binaries, agent-tool invocation rules",
        "2. **Telemetry deny-overlay** — global blocklist that wins over allowlist wildcards (`sparrow.*`, `metrics.*`, `analytics.*`)",
        "3. **Maintainer trust hint** — first-class-vendor vs long-tail signal",
        "4. **Augmentation suggestion** — for skills where Finding L showed augmentation would lift F1, the suggested append-text",
        "5. **Topic-26 compliance metadata** — explicit mapping from this bundle's contents to Professor Monperrus's three subgoals",
        "",
        "## Generated bundles",
        "",
        "| Skill | Predicted hosts | Wildcard residuals | Has augmentation? | Trust tier |",
        "|---|---|---|---|---|",
    ]
    for sid, bundle in bundles.items():
        if "error" in bundle:
            lines.append(f"| {sid} | _missing prediction_ | — | — | — |")
            continue
        n_pred = bundle["headline_metrics_for_this_skill"]["predicted_hosts_count"]
        n_residual = len(bundle["capability_declarations"]["network_egress"]["wildcard_residuals"])
        aug = "yes" if bundle["augmentation_suggestion"]["available"] else "no"
        trust = bundle["maintainer_trust_hint"]["trust_tier"]
        lines.append(f"| `{sid}` | {n_pred} | {n_residual} | {aug} | {trust} |")

    lines.extend([
        "",
        "## Demo bundle: `firebase-hosting-basics-aug/skill-policy.json`",
        "",
        "Best showcase target because it has both (a) substantial declared network surface, (b) the bundled augmentation that lifted Finding L's F1 by 25pp, and (c) a first-class vendor maintainer signal.",
        "",
        "```json",
        json.dumps(bundles.get("firebase-hosting-basics-aug", {"error": "missing"}), indent=2)[:3500],
        "```",
        "",
        "## Deployment shape",
        "",
        "Each generated `skill-policy.json` sits alongside the maintainer-published `SKILL.md`. An installer (skills.sh, Socket, the agent-runtime, or a CI pre-commit hook) reads the bundle at install time and either:",
        "",
        "1. **Translates to enforcement primitive** — emits iptables OUTPUT rules from `network_egress.explicit_allow`, seccomp filters from `subprocess_spawn.binaries`, AppArmor profile from `filesystem_*.predicates`, etc. (per Section 6.1's primitive table).",
        "2. **Surfaces to user for review** — shows the user the declared capability set before the agent runs, with the `non_authoritative_disclaimer` and `maintainer_trust_hint` visible.",
        "3. **Composes with global policy** — the registry-level installer applies its own deny-overlay (additional telemetry suffixes, malicious-host threat-intel feeds, organisation-policy denylists) on top of the per-skill bundle.",
        "",
        "The bundle is *not* a substitute for the SKILL.md; it is a machine-actionable companion artefact. The same way SLSA attestations sit alongside an npm package's `package.json` without replacing it, `skill-policy.json` sits alongside `SKILL.md`. If the maintainer publishes a signed bundle, the deployer can use it directly; if not, an automated tool (this prototype, or Socket's pipeline) can generate one from the SKILL.md text alone.",
        "",
        "## Path to production",
        "",
        "Three layers of trust escalation:",
        "",
        "1. **Auto-generated bundle (this prototype)** — derived from SKILL.md text via LLM extraction; useful as a default-deny baseline; subject to Finding O caveat (the bundle inherits whatever the SKILL.md names, including attacker hosts in adversarial cases).",
        "2. **Maintainer-signed bundle** — the maintainer publishes a `skill-policy.json` themselves with a Sigstore-signed attestation; deployers verify the signature and trust the bundle as the ground-truth declared capabilities.",
        "3. **Registry-curated bundle** — skills.sh, Socket, or an equivalent registry runs the auto-generation pipeline + manual review on every skill; publishes a curated bundle as part of the catalogue. This is the SLSA-shaped supply-chain-attestation pattern.",
        "",
        "Our prototype is at level 1; the report's policy-direction recommendation is to evolve toward level 3 with the maintainer-signed level 2 as a fallback.",
    ])
    out_md.write_text("\n".join(lines) + "\n")
    print(f"=> {out_md}")


if __name__ == "__main__":
    main()
