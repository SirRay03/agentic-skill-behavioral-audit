# Skill Authoring Guide — Closing the Declared-vs-Observed Gap

**For**: maintainers of agentic skills published to skills.sh, GitHub, or vendor registries.
**Source**: empirical findings from a 25-skill behavioural audit (this repository, 2026-05-09). Findings catalogued at `DECISIONS.md`, summarised at `report.md`.

This guide gives skill maintainers six concrete authoring practices that materially close the gap between what a SKILL.md *says* and what an agent loaded with that skill *does at runtime*. Each practice is grounded in a measured finding from the audit.

---

## Why this matters

When a SKILL.md doesn't accurately predict the agent's runtime IO, three things break:

1. **Sandbox-policy generators** (LLM extraction → iptables/seccomp policy) emit allowlists that either over-block (breaks legitimate work) or under-block (lets vendor telemetry through unnoticed).
2. **Pre-install audits** can't tell whether your skill is safe to load without doing dynamic analysis.
3. **Reviewers and security teams** can't verify behaviour from documentation alone.

The audit found a **bimodal F1 distribution**: pure-text and single-output skills achieve F1 ≥ 0.95 between SKILL.md prediction and observed runtime; CLI-wrapping skills concentrate at F1 < 0.10. The gap is mechanical and fixable. Below are the six practices that close it.

---

## 1. Add an "Observed Runtime Endpoints" section to SKILL.md

The largest single F1 lift in our augmentation experiment (Finding L, Section 5.6 of the report) came from adding one new section listing the hosts/paths the wrapped CLI actually contacts. Hosts F1 on `firebase-hosting-basics` jumped from 0.36 to 0.62 with a single paragraph.

Template:

```markdown
## Observed Runtime Endpoints

In addition to the documented services, every invocation of this skill contacts:

- `<host>.<vendor>.<tld>` — what the host is and why it fires (telemetry beacon /
  binary fetch / config probe / API call). Note conditions that suppress the
  call (e.g., "fires unless `--no-telemetry` is passed").
- `~/.config/<vendor>/<file>` — local state the wrapped CLI maintains under the
  user-config directory (NOT under the project workspace).
- `<github-release-asset-url-pattern>` — first-fetch artefacts pulled from
  GitHub Releases. Pin to specific versions if reproducibility matters.

These endpoints are observed via end-to-end syscall + DNS instrumentation; they
belong to the wrapped CLI, not the agent harness loading the skill.
```

This section is the single most useful artefact for anyone deriving sandbox policy from your SKILL.md.

---

## 2. Disclose unconditional telemetry beacons by name

The audit found that **every skill that wraps a CLI emits at least one undocumented vendor-side telemetry beacon** (Finding G). Examples observed:

| Wrapped CLI | Telemetry beacon | Documented in vendor SKILL.md? |
|---|---|---|
| `wrangler` (Cloudflare Workers) | `sparrow.cloudflare.com` | no |
| `semgrep` | `metrics.semgrep.dev` | no |
| `firebase-tools` | `firebase-public.firebaseio.com` | no |

If your skill wraps a CLI that emits a telemetry beacon, **name the beacon explicitly** in the Observed Endpoints section. State the suppression flag if one exists (e.g., `--disable-metrics` for Semgrep). This converts a Finding-G silent-undeclared host into a Finding-L declared-runtime-endpoint, dropping the policy-generator's false-blocked count to zero on the affected skill.

---

## 3. Avoid wildcard hostname predicates

LLM predictors reading a SKILL.md that names `https://api.cloudflare.com` and `https://workers.cloudflare.com` will sometimes generate `*.cloudflare.com` as a wildcard predicate. **Wildcard predicates accidentally admit the telemetry sub-domain** the policy is supposed to block (Finding M). Concretely: a `*.cloudflare.com` allowlist permits both `api.cloudflare.com` (legitimate) AND `sparrow.cloudflare.com` (telemetry).

Mitigation on the SKILL.md side:

- Name specific subdomains (`api.cloudflare.com`, `workers.cloudflare.com`) rather than wildcarding.
- If you write a wildcard, follow it with explicit *exclusions*: "All `*.cloudflare.com` except `sparrow.cloudflare.com` (analytics beacon, not required for skill)."

Mitigation on the policy-generator side: pair the skill-derived allowlist with a global telemetry-suffix deny-overlay that wins over allowlist wildcards (`metrics.*`, `sparrow.*`, `analytics.*`, `*-telemetry.*`). The overlay generalises across vendors and requires only periodic maintenance.

---

## 4. List every bundled sibling and tag its trust-level

The audit found two patterns that cause skill-bundle confusion:

- Skills that bundle a sibling file the SKILL.md never references, where an agent might load it via directory listing (Finding E — `improve-codebase-architecture/DEEPENING.md`).
- Skills that route malicious instructions through bundled siblings the predictor doesn't ingest (mutation suite M4 — `references/telemetry.md`). The predictor sees only the benign-looking SKILL.md and misses the attack.

Best practice:

```markdown
## Bundled siblings

Files in this skill's bundle, by trust level:

- `SKILL.md` — primary contract; canonical maintainer-published.
- `references/configuration.md` — read-only reference; auto-loaded by the
  `Read configuration` workflow step.
- `scripts/setup.sh` — auto-executed by the `setup` workflow step. Contains
  shell commands. Audit before installing.
- `tests/` — for maintainer use; not loaded at agent runtime.
```

Naming each sibling with its trust level (read-only / auto-executed / test-only) lets a pre-install audit operator see the entire trust surface without reading every file.

---

## 5. Document non-canonical state paths

CLIs commonly maintain state outside the project workspace — under `~/.config/<vendor>/`, `~/.cache/<vendor>/`, `~/.<vendor>/`. The audit found these are **systematically omitted** from SKILL.md documentation (Finding C → runtime-config-probe class in the failure-mode taxonomy):

| Vendor CLI | State path | Listed in SKILL.md? |
|---|---|---|
| wrangler | `~/.config/.wrangler/{logs,metrics.json}` | no |
| firebase-tools | `~/.config/configstore/firebase-tools.json`, `~/.cache/firebase/emulators/` | no |
| firecrawl | `~/.config/firecrawl-cli/interact-session.json` | no |

Add these paths to the Observed Endpoints section. This lets sandbox-policy generators correctly classify them (almost always: allow-at-base-policy, since they're agent-runtime concerns, not skill-specific).

---

## 6. Pin downloaded artefacts and disclose binary-fetch CDNs

If your wrapped CLI fetches binary artefacts at first-use (the common pattern for emulator JARs, browser binaries, language toolchains), the fetch destination is a separate trust surface from the npm/pip/go package itself. The audit found `firebase-tools` fetches emulator JARs from `release-assets.githubusercontent.com`, undocumented in SKILL.md.

Best practice: declare both the package source AND the binary-fetch source in your SKILL.md. Where possible, pin versions and provide a SHA-256 hash so the deployment can verify provenance against expected artefacts (SLSA-shaped check — see [slsa.dev](https://slsa.dev/) for the supply-chain provenance framework).

```markdown
## Binary fetches

This skill installs `firebase-tools` from npm (`registry.npmjs.org`). On first
use, the `emulators:start` subcommand fetches additional binaries:

- Hosting emulator JAR: `https://github.com/firebase/firebase-tools/releases/download/v<version>/firebase-emulator-tools-<version>.zip`
  - SHA-256: `<hash>` (verify with `shasum -a 256`)
  - Cached at `~/.cache/firebase/emulators/<version>/`
```

---

## Quick checklist before publishing

- [ ] **Observed Runtime Endpoints** section added with declared hosts and paths
- [ ] **Telemetry beacons** named explicitly with suppression flags
- [ ] **Wildcard predicates** avoided in declared-host lists, OR paired with explicit exclusions
- [ ] **Bundled siblings** listed with trust-level tags
- [ ] **Non-canonical state paths** (`~/.config/<vendor>/`, `~/.cache/<vendor>/`) documented
- [ ] **Binary-fetch CDNs** named with version pins and SHA-256 hashes where possible

A SKILL.md that satisfies all six items lifts the predictor's hosts F1 from below 0.10 (CLI-wrapper cluster baseline) into the 0.6+ range. That is a one-paragraph-of-work change with a substantial security-tooling payoff for downstream consumers.

---

## Empirical bounds — what to expect after augmentation

| Skill | Original hosts F1 | Augmented hosts F1 | SKILL.md change |
|---|---|---|---|
| firebase-hosting-basics | 0.364 | **0.615** | +0.251 F1 (+25.1 pp) from a single appended section (~120 words) |
| wrangler | 0.500 | 0.500 | wildcard already covered telemetry, no F1 lift but writes F1 +0.10 |
| semgrep | 0.571 | 0.571 | predictor already inferred from CLI conventions |

**Pattern**: lift is concentrated in thin SKILL.mds (firebase-hosting-basics, 46 lines) and saturates on detailed ones (semgrep, 321 lines). The cost of authoring the augmentation is low (~30 minutes per skill); the cost to downstream operators of NOT authoring it is the entire failure-mode taxonomy of Findings C, G, and M.

---

## References

### Empirical anchor (this work)

This guidance was derived empirically from the audit shipped in this repository (2026-05-09):
- Headline F1 numbers: `report.md` Section 4 (mean hosts F1 = **0.431** across 25 production skills; aug-inclusive 0.475 [0.399, 0.542] at n=9)
- Augmentation experiment: `report.md` Section 5.6 (Finding L)
- Wildcard sabotage: `report.md` Section 6 (Finding M)
- Failure-mode taxonomy: `analysis/failure-mode-taxonomy.md`
- Mutation-suite detection rates: `analysis/mutation-suite.md` (defense-in-depth 6/6, L1 brittleness drops to 0% under realistic regex per `analysis/mutation-suite-ablation.md`)

For the underlying threat model and defense-layer mapping, see `report.md` Section 2.

### Background literature on agentic-skill supply-chain security

- **Liu et al. (2026) "Agent Skills in the Wild: An Empirical Study of Security Vulnerabilities at Scale"** — [arxiv:2601.10338](https://arxiv.org/abs/2601.10338) — large-scale empirical analysis (n=42,447 collected, 31,132 analysed via SkillScan; 26.1% vulnerable across 14 patterns in 4 categories). This is the headline academic study Professor Monperrus's topic-26 description names.
- **Socket — "Socket Brings Supply Chain Security to skills.sh"** — [socket.dev blog](https://socket.dev/blog/socket-brings-supply-chain-security-to-skills) — deployed registry-scale scanner for skills.sh's 60,000+ catalogue, 94.5%/98.7% precision/recall on known-malicious skills. Industrial counterpart to Liu et al.
- **Professor Monperrus's topic-26 description** ([monperrus.net/martin/topics](https://www.monperrus.net/martin/topics)) — research direction *"Automatic Hardening of Agentic Skills"*: capability-based permission models, sandboxing approaches at different granularities, detection methods combining static analysis with semantic understanding of skill intent.
- **SLSA (Supply-chain Levels for Software Artifacts)** — [slsa.dev](https://slsa.dev/) — provenance ladder referenced in practice 6 above for binary-fetch SHA pinning.
- **Greshake et al. (2023) "Not What You've Signed Up For"** ([arxiv:2302.12173](https://arxiv.org/abs/2302.12173)) — seminal indirect-prompt-injection paper. Practice 4 (bundled-sibling tagging) addresses one variant: maintainer-controlled SKILL.md as the injection vector.
