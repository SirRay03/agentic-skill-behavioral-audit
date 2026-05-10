# Phase 4.7+ — Registry-Level Policy-Bundle Prototype

Concrete demonstration that the SKILL.md → policy direction can ship as a
deployable artefact alongside the SKILL.md itself. For each target skill,
the prototype generates a `skill-policy.json` companion file with five
components:

1. **Capability declarations** — network egress (with wildcard deflation per Finding M), filesystem read/write predicates, subprocess binaries, agent-tool invocation rules
2. **Telemetry deny-overlay** — global blocklist that wins over allowlist wildcards (`sparrow.*`, `metrics.*`, `analytics.*`)
3. **Maintainer trust hint** — first-class-vendor vs long-tail signal
4. **Augmentation suggestion** — for skills where Finding L showed augmentation would lift F1, the suggested append-text
5. **Topic-26 compliance metadata** — explicit mapping from this bundle's contents to Professor Monperrus's three subgoals

## Generated bundles

| Skill | Predicted hosts | Wildcard residuals | Has augmentation? | Trust tier |
|---|---|---|---|---|
| `firebase-hosting-basics-aug` | 9 | 0 | no | first-class-vendor |
| `wrangler` | 6 | 2 | yes | long-tail |
| `semgrep` | 5 | 1 | yes | first-class-vendor |
| `firecrawl-scrape` | 2 | 0 | no | first-class-vendor |
| `auth0-quickstart` | 5 | 1 | no | first-class-vendor |

## Demo bundle: `firebase-hosting-basics-aug/skill-policy.json`

Best showcase target because it has both (a) substantial declared network surface, (b) the bundled augmentation that lifted Finding L's F1 by 25pp, and (c) a first-class vendor maintainer signal.

```json
{
  "skill_policy_schema_version": "0.1-prototype",
  "generated_for_skill_id": "firebase-hosting-basics-aug",
  "generation_method": "Claude Opus 4.7 xhigh-effort SKILL.md-only prediction (predict.py) + wildcard deflation (Finding M post-process)",
  "capability_declarations": {
    "network_egress": {
      "explicit_allow": [
        {
          "host": "firebase-public.firebaseio.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "github.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "release-assets.githubusercontent.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "registry.npmjs.org",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "firebase.googleapis.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "firebasehosting.googleapis.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "hosting.firebaseapp.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "accounts.google.com",
          "source": "literal",
          "type": "exact"
        },
        {
          "host": "oauth2.googleapis.com",
          "source": "literal",
          "type": "exact"
        }
      ],
      "wildcard_residuals": [],
      "telemetry_deny_overlay": [
        "sparrow.cloudflare.com",
        "metrics.semgrep.dev",
        "ogads-pa.clients6.google.com",
        "metrics.*.dev",
        "analytics.*",
        "telemetry.*",
        "*-telemetry.*.com"
      ],
      "policy_decision_rule": "deny-overlay wins over allowlist wildcards; explicit_allow entries are admitted unconditionally; wildcard_residuals are subject to runtime configuration (default: reject if subdomain_bounded_to is null, else admit only the listed subdomains)."
    },
    "filesystem_read": {
      "predicates": [
        "./firebase.json",
        "./.firebaserc",
        "./public/*",
        "~/.config/configstore/firebase-tools.json",
        "~/.config/configstore/update-notifier-firebase-tools.json",
        "~/.cache/firebase/emulators/*",
        "./references/*.md"
      ],
      "scope": "workdir-relative + ~/.config/<vendor>/* per Finding D"
    },
    "filesystem_write": {
      "predicates": [
        "./firebase.json",
        "./.firebaserc",
        "~/.config/configstore/firebase-tools.json",
        "~/.config/configstore/update-notifier-firebase-tools.json",
        "~/.cache/firebase/emulators/*",
        "./.firebase/*"
      ],
      "scope": "workdir-relative; reject everything outside"
    },
    "subprocess_spawn": {
      "binaries": [
        "npx",
        "node",
        "firebase",
        "firebase-tools"
      ],
      "scope": "execve allowlist; reject other binaries"
    },
    "agent_tool_invocation": {
      "note": "Read from SKILL.md frontmatter `allowed-tools` if declared; otherwise the agent-runtime base policy applies.",
      "example_existing_skills_with_declared_allowed_tools": [
        "gha-security-review"
      ]
    }
  },
  "maintainer_trust_hint": {
    "maintainer_signal_from_skill_id": "firebase",
    "trust_tier": "first-class-vendor",
    "note": "In a deployed registry, maintainer identity should come from a separate signed assertion \u2014 Sigstore for OSS skills, an attest
```

## Deployment shape

Each generated `skill-policy.json` sits alongside the maintainer-published `SKILL.md`. An installer (skills.sh, Socket, the agent-runtime, or a CI pre-commit hook) reads the bundle at install time and either:

1. **Translates to enforcement primitive** — emits iptables OUTPUT rules from `network_egress.explicit_allow`, seccomp filters from `subprocess_spawn.binaries`, AppArmor profile from `filesystem_*.predicates`, etc. (per Section 6.1's primitive table).
2. **Surfaces to user for review** — shows the user the declared capability set before the agent runs, with the `non_authoritative_disclaimer` and `maintainer_trust_hint` visible.
3. **Composes with global policy** — the registry-level installer applies its own deny-overlay (additional telemetry suffixes, malicious-host threat-intel feeds, organisation-policy denylists) on top of the per-skill bundle.

The bundle is *not* a substitute for the SKILL.md; it is a machine-actionable companion artefact. The same way SLSA attestations sit alongside an npm package's `package.json` without replacing it, `skill-policy.json` sits alongside `SKILL.md`. If the maintainer publishes a signed bundle, the deployer can use it directly; if not, an automated tool (this prototype, or Socket's pipeline) can generate one from the SKILL.md text alone.

## Path to production

Three layers of trust escalation:

1. **Auto-generated bundle (this prototype)** — derived from SKILL.md text via LLM extraction; useful as a default-deny baseline; subject to Finding O caveat (the bundle inherits whatever the SKILL.md names, including attacker hosts in adversarial cases).
2. **Maintainer-signed bundle** — the maintainer publishes a `skill-policy.json` themselves with a Sigstore-signed attestation; deployers verify the signature and trust the bundle as the ground-truth declared capabilities.
3. **Registry-curated bundle** — skills.sh, Socket, or an equivalent registry runs the auto-generation pipeline + manual review on every skill; publishes a curated bundle as part of the catalogue. This is the SLSA-shaped supply-chain-attestation pattern.

Our prototype is at level 1; the report's policy-direction recommendation is to evolve toward level 3 with the maintainer-signed level 2 as a fallback.
