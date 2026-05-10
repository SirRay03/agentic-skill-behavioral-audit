#!/usr/bin/env python3
"""Phase 1.F — Network-gap failure-mode taxonomy.

Classify every skill-attributable observed host into one of 7 categories,
then count per category, mark which were declared (in any prediction.json)
vs undeclared, and emit a count table + JSON suitable for a sunburst plot.

Categories:
  - telemetry-beacon          : emits telemetry/metrics, often unconditionally
  - binary-fetch-CDN          : downloads binary artifacts (release JARs, packages)
  - post-auth-API             : requires authentication, performs business operations
  - runtime-config-probe      : queries config/metadata at startup
  - pkg-registry              : language package registry (npm, pypi)
  - auth-token-exchange       : OAuth / token-exchange endpoints
  - external-target           : the user-specified target of the skill's verb
                                (e.g., news.ycombinator.com for agent-browser)

The classification is hand-curated based on each host's role in the trace and
documented behaviour. Expandable by editing CLASSIFY below.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

AGENT_INFRA = {
    "api.anthropic.com", "downloads.claude.ai", "mcp-proxy.anthropic.com",
    "http-intake.logs.us5.datadoghq.com", "chatgpt.com", "ab.chatgpt.com",
    "ipv4only.arpa", "localhost",
}

# Per-host classification. Keyed on the lowercased FQDN.
CLASSIFY = {
    # Telemetry beacons (Findings G, M)
    "sparrow.cloudflare.com": ("telemetry-beacon", "Cloudflare wrangler telemetry, fires unconditionally"),
    "metrics.semgrep.dev": ("telemetry-beacon", "Semgrep usage telemetry, fires per scan"),
    "ogads-pa.clients6.google.com": ("telemetry-beacon", "Google Ads/analytics beacon (Chromium-implied)"),

    # Binary-fetch CDNs
    "release-assets.githubusercontent.com": ("binary-fetch-CDN", "GitHub Releases binary attachments (firebase emulator JARs)"),
    "raw.githubusercontent.com": ("binary-fetch-CDN", "Raw source/binary fetch (web-search inferencesh package)"),
    "dist.inference.sh": ("binary-fetch-CDN", "inference.sh CLI binary distribution"),
    "github.com": ("binary-fetch-CDN", "Code/binary repository (release-asset & raw fetches dispatch through here)"),
    "add-skill.vercel.sh": ("binary-fetch-CDN", "skills.sh installer dispatch (returns install scripts/binaries)"),

    # Post-auth APIs
    "api.firecrawl.dev": ("post-auth-API", "Firecrawl scrape API, requires FIRECRAWL_API_KEY"),
    "firebase.googleapis.com": ("post-auth-API", "Firebase Management API (real-creds unlocks)"),
    "semgrep.dev": ("post-auth-API", "Semgrep rule registry / authenticated lookups"),

    # Runtime config probes
    "firebase-public.firebaseio.com": ("runtime-config-probe", "Firebase Realtime DB public-config startup probe"),
    "android.clients.google.com": ("runtime-config-probe", "Chromium platform config probe"),
    "clients2.google.com": ("runtime-config-probe", "Chromium component update check"),
    "play.google.com": ("runtime-config-probe", "Chromium/Play Services config"),
    "www.gstatic.com": ("runtime-config-probe", "Google static assets / Chromium runtime"),
    "mtalk.google.com": ("runtime-config-probe", "Google Cloud Messaging endpoint (Chromium GCM keepalive)"),

    # Package registries
    "registry.npmjs.org": ("pkg-registry", "npm package registry"),

    # Auth token exchange
    "accounts.google.com": ("auth-token-exchange", "Google OAuth account endpoint"),
    "www.googleapis.com": ("auth-token-exchange", "Google API discovery + token exchange"),
    "content-autofill.googleapis.com": ("auth-token-exchange", "Chromium autofill API (Google-account scoped)"),

    # External target hosts (the user-specified target of the skill's verb)
    "news.ycombinator.com": ("external-target", "user-specified scrape target for agent-browser"),
    "www.google.com": ("external-target", "Chromium default-page navigation"),
    "skills.sh": ("external-target", "find-skills user-targeted catalogue host"),
}


def host_admits_predicate(host: str, allowlist: list[str]) -> bool:
    """Mirrors policy-eval.py."""
    h = host.lower()
    for p in allowlist:
        p_l = p.lower()
        if p_l == h:
            return True
        if p_l.startswith("*."):
            if h.endswith("." + p_l[2:]) or h == p_l[2:]:
                return True
        if "." in p_l and not p_l.startswith("*"):
            if h == p_l or h.endswith("." + p_l):
                return True
    return False


def main() -> None:
    skills_dir = PROJECT_ROOT / "skills"
    skill_ids = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
    skill_ids = [s for s in skill_ids if not s.endswith("-aug") and not s.startswith("zz-")]

    # host -> list of {skill, trace_variant, declared_by_skills_predictors}
    # The methodologically right question is: "for this (host, skill) pair where the
    # skill's invocation contacted the host, did the skill's OWN predictor declare it?"
    host_observations = defaultdict(list)  # host -> [(skill, trace_variant, declared_in_predictors)]
    host_skill_declared = defaultdict(set)  # host -> set of (skill, predictor) pairs where declared

    for sid in skill_ids:
        sd = skills_dir / sid
        # Load the three predictions for THIS skill
        skill_predictions = {}
        for predictor_name, pred_path in [
            ("orig", sd / "prediction.json"),
            ("fresh", Path("/tmp/fresh-predictor-batch") / "outputs" / "claude-fresh" / sid / "prediction-fresh.json"),
            ("codex", Path("/tmp/fresh-predictor-batch") / "outputs" / "codex-fresh" / sid / "prediction-codex.json"),
        ]:
            if not pred_path.exists():
                continue
            try:
                pred = json.loads(pred_path.read_text())
                skill_predictions[predictor_name] = pred.get("hosts", [])
            except json.JSONDecodeError:
                continue

        # Now go through observed hosts in this skill's traces and check declared by skill's own predictors
        for trace_name in ("trace.json", "trace-codex.json", "trace-realcreds.json"):
            p = sd / trace_name
            if not p.exists():
                continue
            t = json.loads(p.read_text())
            for h in t.get("net", {}).get("dns_queries", []):
                key = h.lower()
                if key in AGENT_INFRA:
                    continue
                # which of THIS skill's predictors declared this host?
                declared_in = []
                for predictor_name, allowlist in skill_predictions.items():
                    if host_admits_predicate(key, allowlist):
                        declared_in.append(predictor_name)
                        host_skill_declared[key].add((sid, predictor_name))
                host_observations[key].append((sid, trace_name, declared_in))

    # Per-host classification + declared status
    host_declared_in = defaultdict(set)  # host -> set of predictor names where any skill+predictor declared it
    for h, sk_preds in host_skill_declared.items():
        for (sid, pred_name) in sk_preds:
            host_declared_in[h].add(pred_name)

    # Build per-host record
    per_host = []
    for h, obs in sorted(host_observations.items()):
        category, why = CLASSIFY.get(h, ("uncategorised", "needs manual classification"))
        declared_by = sorted(host_declared_in.get(h, set()))
        per_host.append({
            "host": h,
            "category": category,
            "why": why,
            "n_traces": len(obs),
            "trace_sources": [f"{s}/{t}" for s, t, _ in obs[:5]],
            "declared_in": declared_by,
            "n_predictors_declared": len(declared_by),
        })

    # Counts per category
    cat_counts = Counter(r["category"] for r in per_host)
    cat_declared = {cat: 0 for cat in cat_counts}
    cat_undeclared = {cat: 0 for cat in cat_counts}
    for r in per_host:
        if r["n_predictors_declared"] > 0:
            cat_declared[r["category"]] += 1
        else:
            cat_undeclared[r["category"]] += 1

    out_dir = PROJECT_ROOT / "analysis"
    out_json = {
        "per_host": per_host,
        "category_counts": dict(cat_counts),
        "category_declared": cat_declared,
        "category_undeclared": cat_undeclared,
    }
    (out_dir / "failure-mode-taxonomy.json").write_text(json.dumps(out_json, indent=2))

    # Markdown
    lines = [
        "# Phase 1.F — Network-Gap Failure-Mode Taxonomy",
        "",
        f"Total distinct skill-attributable observed hosts (across all traces): **{len(per_host)}**",
        "",
        "## Counts per category — declared vs undeclared",
        "",
        "*'Declared' = the host is present in at least one of the three predictor outputs",
        "(orig-Claude, fresh-Claude, Codex), under suffix-aware predicate matching.",
        "'Undeclared' = absent from all three.*",
        "",
        "| Category | Total observed | Declared by ≥1 predictor | Undeclared by all 3 |",
        "|---|---|---|---|",
    ]
    for cat in ["telemetry-beacon", "binary-fetch-CDN", "post-auth-API",
                "runtime-config-probe", "pkg-registry", "auth-token-exchange",
                "external-target", "uncategorised"]:
        if cat in cat_counts:
            lines.append(f"| {cat} | {cat_counts[cat]} | {cat_declared[cat]} | {cat_undeclared[cat]} |")
    lines.append(f"| **Total** | **{sum(cat_counts.values())}** | "
                 f"**{sum(cat_declared.values())}** | **{sum(cat_undeclared.values())}** |")
    lines.append("")

    # Per-host table
    lines.extend([
        "## Per-host detail",
        "",
        "| Host | Category | Declared by | n traces | Why |",
        "|---|---|---|---|---|",
    ])
    for r in per_host:
        decl = ",".join(r["declared_in"]) or "**none (Finding C/G)**"
        lines.append(f"| `{r['host']}` | {r['category']} | {decl} | {r['n_traces']} | {r['why']} |")

    # Defenses per category
    lines.extend([
        "",
        "## Defense recommendation per category",
        "",
        "Different gap classes need different defenses:",
        "",
        "| Category | Best defense |",
        "|---|---|",
        "| telemetry-beacon | **Known-suffix deny-overlay** that wins over allowlist wildcards (Finding M). `metrics.*`, `sparrow.*`, `*-telemetry.*` patterns. |",
        "| binary-fetch-CDN | **SLSA / in-toto provenance** check on fetched artifacts; pin to known-hash. Treat as supply-chain risk, not network-policy risk. |",
        "| post-auth-API | **Recoverable via real-creds runs** — already partially demonstrated for firebase. Stub-creds traces are a strict lower bound. |",
        "| runtime-config-probe | **Allow at base policy level** — these are agent-runtime concerns (Chromium, Firebase tools), not skill-specific. |",
        "| pkg-registry | **Allow at base policy level** — `registry.npmjs.org` and equivalents are universal infrastructure. |",
        "| auth-token-exchange | **Allow at base policy level** alongside pkg-registry; tightly scoped per OAuth provider. |",
        "| external-target | **Skill-specific allowlist** — must be admitted because the user is asking the skill to access the target. Pre-deploy review for trust. |",
        "",
        "## Implication for Section 5 of the report",
        "",
        "The 77% legit-allow / 50% telemetry-catch headline is a sum across these categories;",
        "decomposing reveals where each defense layer pays its way. Specifically:",
        "",
        "- **Telemetry-beacons are the only category where the LLM-derived allowlist consistently fails** (because predictors emit wildcard patterns that accidentally match the telemetry subdomain — Finding M). The deny-overlay fixes this without dynamic instrumentation.",
        "- **Binary-fetch-CDNs** are present in the trace but represent supply-chain risk (e.g., a compromised github.com release-asset would deliver malware to firebase-tools), not policy-violation risk. Different defense layer entirely.",
        "- **Post-auth-APIs** are *correctly under-observed* in stub-creds runs; the real-creds variant work showed they unlock under authentication. Lower-bound framing of the trace data is empirically validated.",
        "- **Runtime-config-probes, pkg-registry, auth-token-exchange** belong in an agent-runtime base policy, not in skill-specific allowlists. Putting them in skill-specific allowlists is the source of most false-positive-block events.",
        "",
        "This decomposition is the pragmatic recommendation that ships with the SKILL.md → policy generator: the per-skill allowlist should not enumerate hosts that belong in the base policy.",
    ])

    (out_dir / "failure-mode-taxonomy.md").write_text("\n".join(lines) + "\n")
    print(f"=> {out_dir}/failure-mode-taxonomy.json")
    print(f"=> {out_dir}/failure-mode-taxonomy.md")
    print()
    print(f"Total distinct hosts: {len(per_host)}")
    print(f"\nCategory counts:")
    for cat, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:25s}  total={n}  declared={cat_declared[cat]}  undeclared={cat_undeclared[cat]}")


if __name__ == "__main__":
    main()
