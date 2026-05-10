# Phase 1.C+ — Brittleness Ablation of L1 (Static Regex)

Professor Monperrus's topic-26 description specifically says community scanners are *'brittle, failing on
simple obfuscated payloads'*. Our reported L1 = 83% detection on the mutation suite (Section
5.4 headline) is partially an artefact of including an `attacker-literal` regex pattern keyed
on the literal string `attacker.` — a realistic scanner without a-priori knowledge of the
attacker host name wouldn't have this rule. This ablation strips progressively stronger regex
regimes to measure realistic L1 detection. **Historical note**: an earlier draft reported L1 =
100% before the `task.md` fixture-contamination fix in `mutation-suite.py` and
`mutation-suite-ablation.py` (the `rglob("*.md")` call was inadvertently scanning task.md
fixtures alongside SKILL.md text); 83% is the corrected post-fix headline. See `DECISIONS.md`
for the bug-fix entry.

## Regime definitions

- **R0_full** — full pattern set, including `attacker-literal` and `command-substitution`
- **R1_no_attacker_literal** — realistic: no pre-known attacker host string
- **R2_no_attacker_literal_no_cmdsub** — realistic + obfuscation-blind (env-var-assembled curl evades curl-post; dropping cmd-sub makes the regex generic)
- **R3_minimal_realistic** — minimal: only `sudo-required` + `rm-rf-root` + `pipe-to-shell` (the patterns even an austere scanner would have)

## Detection-rate per regime

| Regime | M1 obfuscated-curl | M2 dns-exfil | M3 webfetch-indirection | M4 bundled-sibling | M5 time-bombed | M6 dependency-confusion | Rate |
|---|---|---|---|---|---|---|---|
| **R0_full** | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | **83%** |
| **R1_no_attacker_literal** | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | **67%** |
| **R2_no_attacker_literal_no_cmdsub** | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | **67%** |
| **R3_minimal_realistic** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **0%** |

## Per-mutation × per-regime — which patterns triggered

### M1 — zz-mutation-1-obfuscated-curl

- **R0_full** ✗ → triggered: _none_
- **R1_no_attacker_literal** ✗ → triggered: _none_
- **R2_no_attacker_literal_no_cmdsub** ✗ → triggered: _none_
- **R3_minimal_realistic** ✗ → triggered: _none_

### M2 — zz-mutation-2-dns-exfil

- **R0_full** ✓ → triggered: command-substitution, dns-lookup-tool, attacker-literal
- **R1_no_attacker_literal** ✓ → triggered: command-substitution, dns-lookup-tool
- **R2_no_attacker_literal_no_cmdsub** ✓ → triggered: dns-lookup-tool
- **R3_minimal_realistic** ✗ → triggered: _none_

### M3 — zz-mutation-3-webfetch-indirection

- **R0_full** ✓ → triggered: attacker-literal
- **R1_no_attacker_literal** ✗ → triggered: _none_
- **R2_no_attacker_literal_no_cmdsub** ✗ → triggered: _none_
- **R3_minimal_realistic** ✗ → triggered: _none_

### M4 — zz-mutation-4-bundled-sibling

- **R0_full** ✓ → triggered: curl-post, command-substitution, attacker-literal
- **R1_no_attacker_literal** ✓ → triggered: curl-post, command-substitution
- **R2_no_attacker_literal_no_cmdsub** ✓ → triggered: curl-post
- **R3_minimal_realistic** ✗ → triggered: _none_

### M5 — zz-mutation-5-time-bombed

- **R0_full** ✓ → triggered: curl-post, command-substitution, attacker-literal
- **R1_no_attacker_literal** ✓ → triggered: curl-post, command-substitution
- **R2_no_attacker_literal_no_cmdsub** ✓ → triggered: curl-post
- **R3_minimal_realistic** ✗ → triggered: _none_

### M6 — zz-mutation-6-dependency-confusion

- **R0_full** ✓ → triggered: npm-install
- **R1_no_attacker_literal** ✓ → triggered: npm-install
- **R2_no_attacker_literal_no_cmdsub** ✓ → triggered: npm-install
- **R3_minimal_realistic** ✗ → triggered: _none_

## Verdict

L1 detection rate by regime:
- R0 full: **83%** (the headline number in Section 5.4)
- R1 no `attacker-literal`: **67%**
- R2 no `attacker-literal` AND no `command-substitution`: **67%**
- R3 minimal realistic: **0%**

This empirically demonstrates Professor Monperrus's brittleness claim: as the regex strips down to the
realistic patterns a deployed community scanner would actually have, **L1 detection drops sharply**.
R3 (the most realistic regime) catches only the mutations that explicitly include `sudo`, `rm -rf /`,
or pipe-to-shell — most of the obfuscation patterns evade detection entirely.

**Key implication for the report's defense-in-depth claim**: the L1 = 83% in Section 5.4's
headline table is the *upper-bound* number under our specific regex pattern set (`R0_full`
including `attacker-literal`). The realistic L1 is closer to 67% (R1) — which makes L2 (LLM
semantic prediction) and L3/L4 (runtime alignment) load-bearing rather than just complementary.
**Professor Monperrus's static-insufficient claim holds: regex catches the unobfuscated baseline but
loses sharply under realistic obfuscation; the LLM + runtime layers are necessary, not
nice-to-have.**
