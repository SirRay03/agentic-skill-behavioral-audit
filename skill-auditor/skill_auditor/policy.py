"""Policy-bundle generator. Mirrors agentic-skill-behavioral-audit/analysis/policy-bundle-generator.py
but exposes the build function as an importable callable."""
from __future__ import annotations
import json
from pathlib import Path


TELEMETRY_SUFFIX_DENY = [
    "sparrow.cloudflare.com",
    "metrics.semgrep.dev",
    "ogads-pa.clients6.google.com",
    "metrics.*.dev",
    "analytics.*",
    "telemetry.*",
    "*-telemetry.*.com",
]

TRUSTED_MAKERS = {
    "anthropics", "anthropic", "cloudflare", "firebase", "vercel-labs",
    "microsoft", "google", "auth0", "getsentry", "semgrep", "prisma",
    "pinecone-io", "replicate", "browserbase", "firecrawl", "openai",
}

AGENT_INFRA = {
    "api.anthropic.com", "downloads.claude.ai", "mcp-proxy.anthropic.com",
    "http-intake.logs.us5.datadoghq.com", "chatgpt.com", "ab.chatgpt.com",
    "ipv4only.arpa", "localhost",
}


def deflate_wildcards(allowlist: list[str], observed_hosts: list[str]) -> dict:
    deflated = []
    residual_wildcards = []
    for pred in allowlist:
        if pred.startswith("*."):
            suffix = pred[2:]
            specific = sorted({
                h.lower() for h in observed_hosts
                if h.lower().endswith("." + suffix) or h.lower() == suffix
            })
            if specific:
                for sub in specific:
                    deflated.append({"host": sub, "predicate": pred,
                                     "source": "wildcard-deflated", "type": "exact"})
                residual_wildcards.append({
                    "host_pattern": pred,
                    "subdomain_bounded_to": specific,
                    "type": "wildcard-bounded",
                })
            else:
                residual_wildcards.append({
                    "host_pattern": pred,
                    "subdomain_bounded_to": None,
                    "type": "wildcard-unconstrained",
                    "note": "no observed subdomain matches; runtime should reject by default",
                })
        else:
            deflated.append({"host": pred, "source": "literal", "type": "exact"})
    return {"explicit_subdomains": deflated, "residual_wildcards": residual_wildcards}


def maker_trust_hint(skill_id: str) -> dict:
    matched = None
    trust_tier = "long-tail"
    for trusted in TRUSTED_MAKERS:
        if trusted in skill_id.lower():
            trust_tier = "first-class-vendor"
            matched = trusted
            break
    return {
        "maintainer_signal_from_skill_id": matched,
        "trust_tier": trust_tier,
        "note": ("In a deployed registry, maintainer identity should come from "
                 "a separate signed assertion — Sigstore for OSS skills, an "
                 "attestation chain for enterprise skills."),
    }


def build_policy_bundle(*, skill_id: str, prediction_path: Path,
                        trace_path: Path | None = None) -> dict:
    pred = json.loads(prediction_path.read_text(encoding="utf-8"))
    observed_hosts = []
    if trace_path is not None and trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        observed_hosts = trace.get("net", {}).get("dns_queries", [])

    network = deflate_wildcards(pred.get("hosts", []), observed_hosts)

    return {
        "skill_policy_schema_version": "0.1-prototype",
        "generated_for_skill_id": skill_id,
        "generation_method": ("LLM-extracted SKILL.md prediction + wildcard deflation "
                              "(Finding M post-process)"),
        "capability_declarations": {
            "network_egress": {
                "explicit_allow": network["explicit_subdomains"],
                "wildcard_residuals": network["residual_wildcards"],
                "telemetry_deny_overlay": TELEMETRY_SUFFIX_DENY,
                "policy_decision_rule": (
                    "deny-overlay wins over allowlist wildcards; explicit_allow "
                    "entries are admitted unconditionally; wildcard_residuals are "
                    "subject to runtime configuration."
                ),
            },
            "filesystem_read": {
                "predicates": pred.get("paths_read", []),
                "scope": "workdir-relative + ~/.config/<vendor>/* per Finding D",
            },
            "filesystem_write": {
                "predicates": pred.get("paths_written", []),
                "scope": "workdir-relative; reject everything outside",
            },
            "subprocess_spawn": {
                "binaries": pred.get("subprocesses", []),
                "scope": "execve allowlist; reject other binaries",
            },
            "agent_tool_invocation": {
                "note": "Read from SKILL.md frontmatter `allowed-tools` if declared.",
            },
        },
        "maintainer_trust_hint": maker_trust_hint(skill_id),
        "headline_metrics_for_this_skill": {
            "predicted_hosts_count": len(pred.get("hosts", [])),
            "observed_skill_attributable_hosts": [
                h for h in observed_hosts if h not in AGENT_INFRA
            ],
        },
        "non_authoritative_disclaimer": (
            "This bundle is generated automatically and is not a substitute for "
            "the maintainer-published SKILL.md. It is intended to be installed "
            "alongside the SKILL.md, not in place of it."
        ),
    }
