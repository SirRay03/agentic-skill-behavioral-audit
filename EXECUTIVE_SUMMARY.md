# Executive Summary — A Dynamic Behavioural Auditor for Agentic Skills

**Author**: Rayhan Putra · KTH MSc Cybersecurity (Autumn 2026 admit) · ITB STI 2021
**For**: Professor Monperrus, KTH ASSERT
**Date**: 2026-05-11

## In one paragraph

This is the entry-point exercise for Professor Monperrus's open thesis topic *"Automatic Hardening of Agentic Skills"* — anchored explicitly to the topic-26 references [Liu et al. (2026) "Agent Skills in the Wild"](https://arxiv.org/abs/2601.10338) (n=42,447 skills, 26.1% vulnerable across 4 categories) and [Socket's deployed skills.sh scanner](https://socket.dev/blog/socket-brings-supply-chain-security-to-skills) (60,000+ skills, 94.5%/98.7% precision/recall). Both establish the problem at registry scale; this work is the depth-instrumentation complement. For 25 publicly-published "agentic skills" (markdown contracts that ship with prompt instructions for AI coding agents), I captured the runtime filesystem and network footprint of one representative invocation under Claude Code, then compared the trace against an LLM's prediction made from the SKILL.md text alone. The headline empirical claim: **CLI-wrapping skills systematically under-declare their network surface** (mean hosts F1 = 0.475, 95% CI [0.399, 0.542]; bimodal F1 distribution, Mann-Whitney p = 0.030 for the bimodal-cluster split). Cross-agent control under OpenAI's Codex CLI confirms the gap reproduces across agent harnesses; cross-LLM predictor variance (Jaccard 0.41 on hosts) is materially larger than context-contamination variance (0.72), making the LLM-of-prediction a load-bearing methodological parameter. As a constructive direction, a SKILL.md-derived egress allowlist using the LLM extraction as policy artifact admits 77% of legitimate observed traffic and flags 50% of total traffic as undeclared on the eight skills with non-empty network surface — answering "yes, sandbox policy can be derived from skill markdown alone, conditional on a wildcard-deflation post-process and a maintainer-reputation gate." A policy-enforcement simulation on three skills shows zero false-positive blocks under the derived allowlist; an adversarial mutation suite (six attack patterns × four defense layers) shows 6/6 mutations contained by defense-in-depth across (static regex, LLM predictor, Claude runtime, Codex runtime).

## The five strongest findings

1. **Vendor-CLI under-declaration** (Findings C, G). Every CLI-wrapping skill in the sample emits at least one undeclared host or telemetry beacon — `sparrow.cloudflare.com` for wrangler, `metrics.semgrep.dev` for semgrep, `firebase-public.firebaseio.com` for firebase-tools. The gap is in the wrapped CLI, not the skill maintainer.
2. **Agentic-not-architectural blind spots** (Finding A reshaped). Both Claude Code and Codex CLI on the wrangler task ignore SKILL.md's "prefer retrieval" directive and skip `developers.cloudflare.com`. The blind spot is *agent-behavioural* (pre-training already contains the answer), not instrumentation-architectural.
3. **Defense-in-depth empirically validated** (Findings I+J+K, mutation suite Phase 1.C). Across six attack mutations × four defense layers, all six attacks contained by at least one layer: static regex 100%, LLM predictor 67%, Claude runtime 100%, Codex runtime 100%. Predictor misses (M4 bundled-sibling, M6 dependency-confusion) point at concrete, implementable predictor extensions.
4. **Adversarial-maintainer threat is real** (Finding O, NEW from Phase 1.A). All three predictor sources (orig-Claude, fresh-Claude, Codex) emit `attacker.example.com` in their structured `hosts` field for the synthetic adversarial demo. Structured-extraction policy generators are *safety-blind by construction*; they faithfully encode whatever the SKILL.md names, including attacker hosts. Defense-in-depth is necessary, not optional.
5. **Bimodal F1 distribution is a property of skill class, not maker** (Finding C+G + subgroup analysis Phase 3.M). CLI-wrapper vs pure-text/single-output skills differ significantly on paths_read F1 (Mann-Whitney U=6, p=0.030). Maker organisation, skill category, and SKILL.md length quartile do *not* explain the distribution variance — the bimodal split is mechanical, predictable, and addressable by skill maintainer practice.

## Headline numbers (n=25)

| Metric | Value (95% CI) |
|---|---|
| Hosts F1 | 0.475 [0.399, 0.542] |
| paths_read F1 | 0.368 [0.185, 0.548] |
| paths_written F1 | 0.375 [0.235, 0.543] |
| LLM predictor recall vs static regex baseline | 2.50× (Wilcoxon p=0.047, McNemar's p=0.003) |
| Policy-enforcement simulation: legit-allow rate | 77% (n=8 skills, 3-of-3 would-complete under enforcement) |
| Policy-enforcement simulation: telemetry-catch | 50% (13/26 hosts correctly flagged as undeclared) |
| Mutation suite defense-in-depth coverage | 6 of 6 contained (L1 83% / L2 67% / L3 100% / L4 100%; L1 drops to 0% under minimal-realistic regex per ablation) |
| Cross-LLM Jaccard on hosts axis (orig-Claude vs Codex) | 0.41 |

## Constructive answer to Professor Monperrus's research question

**Yes, sandbox policy can be derived from skill markdown alone**, subject to three composition requirements:

- **Wildcard deflation** (Finding M): the predictor's `*.cloudflare.com` accidentally admits the telemetry sub-domain `sparrow.cloudflare.com`. Post-process the prediction to either expand wildcards into explicit subdomains or pair with a global telemetry-suffix deny-overlay.
- **Maintainer-reputation gate** (Finding O): structured-extraction policy generators inherit maintainer-supplied malice. Pair the SKILL.md-derived allowlist with a separate trust check before deployment.
- **Per-agent baseline subtraction** (Finding H): syscall-trace cross-agent comparisons are dominated by per-agent bootstrap costs, not per-task work. Subtract baselines before per-(skill, agent) policy generation.

The empirical bound on the constructive direction: 77% legitimate-allow / 50% telemetry-catch on n=8 skills with non-empty network surface, with the wildcard-deflation post-process and maintainer-reputation gate as necessary follow-ups.

## Methodology spine

- 25 production skills + 1 synthetic adversarial demo + 6 attack-pattern mutations + 3 augmented-SKILL.md variants
- 3 prediction sources per skill: orig-Claude (with project context, xhigh effort), fresh-Claude (clean home, xhigh), Codex CLI (clean home, default effort)
- Cross-agent dynamic on 7 skills via Codex
- Real-creds variants for 3 cred-gated skills (firebase, wrangler, firecrawl)
- Static regex baseline (recall 0.27) vs LLM predictor (recall 0.68); McNemar's confirms asymmetry at p=0.003
- Bootstrap 95% CIs on every reported aggregate metric
- 16 findings (A–O) catalogued; 3 structural patterns; layered-policy-stack defense architecture

## Future work

1. Cross-agent on the full 25-skill sample (currently n=7).
2. TLS interception via mitmproxy for URL-path / payload comparison.
3. Live policy-enforcement deployment via iptables in privileged sandbox (recipe documented; deferred from this work for sandbox-isolation reasons).
4. Predictor extensions for the two L2 misses: bundled-sibling ingestion (M4) and named-subprocess provenance check (M6).
5. Tetragon/Falco-class runtime observability for CI-integrated per-skill-PR audit.
6. Skill-author guidance roll-out — see `SKILL_AUTHORING_GUIDE.md` for the six-practice checklist derived empirically from this work.

## Repository

Full report: `report.md` (≈14 pages). Methodology: `methodology.md`. Decision log: `DECISIONS.md`. Per-finding analyses: `analysis/{stats,policy-eval,policy-enforcement,mutation-suite,failure-mode-taxonomy,predictor-vs-truth,subgroup-analysis,mechanism-investigation,citation-justifications}.md`. Skill-author guidance: `SKILL_AUTHORING_GUIDE.md`. Visualisations: `figures/fig-{01..06}.{svg,png}`.

Total token cost: ~$50 of subscription budget across Anthropic Claude Code + OpenAI Codex CLI subscriptions. Out-of-pocket cost: $0.
