# Citation Justifications — Section 2 of the Report

For each citation in `report.md` Section 2.1 (Related work), this document records:
- **Where**: which subsection of Section 2.1 cites it
- **What claim it supports** in the report
- **Why credible**: peer review / venue / institutional backing
- **Why this specific paper**: why this citation rather than a substitute
- **Verification**: how I confirmed the citation details (web-search, prior knowledge, or marked uncertain)

Cited works are grouped by Section 2.1's five literatures.

---

## A. Capability-based security and POLA

### A.1 — Saltzer, J. H., & Schroeder, M. D. (1975). "The Protection of Information in Computer Systems." *Proceedings of the IEEE*, 63(9), 1278-1308.

- **Where in the report**: Section 2.1, opening sentence of capability-based-security paragraph
- **Claim it supports**: that "least-privilege" is a foundational principle — each component should run with only the capabilities it requires
- **Why credible**: This is *the* foundational paper of computer security. Cited >10,000 times. POLA is one of the eight design principles enumerated in this paper and remains the canonical framing of access-control architecture.
- **Why this specific paper**: it is the canonical source for the principle of least authority. Any security work that argues "derive least-privilege from X" needs to ground in this paper.
- **In OUR report**: it grounds the central design question — *what capabilities does this component actually need?* — that motivates our SKILL.md → policy direction. Without this anchor, our policy generator would be a tool without a tradition.
- **Verification**: prior knowledge; the paper is accessible at IEEE Xplore. The Section 6.3.A.6 enumeration of design principles is well-known and includes "Least Privilege."

### A.2 — Watson, R. N. M., Anderson, J., Laurie, B., & Kennaway, K. (2010). "Capsicum: Practical Capabilities for UNIX." *USENIX Security '10*.

- **Where in the report**: Section 2.1, capability-based-security paragraph (sentence 2)
- **Claim it supports**: that POLA can be operationalised on modern OSes via per-process capability scoping
- **Why credible**: USENIX Security is a tier-1 systems-security venue. Capsicum is shipped in FreeBSD and influenced Linux's capability model. >700 citations.
- **Why this specific paper**: it is the canonical bridge from theoretical capability-based security (Saltzer & Schroeder) to a working POSIX-compatible implementation. Our work continues this bridge into the agentic-skills setting.
- **In OUR report**: positions our work as continuing the practical-capability tradition. The agentic-skills setting is Capsicum's question (per-process capability scoping) one layer up — per-skill scoping, where the "process" is now an LLM-powered agent loaded with a specific skill.
- **Verification**: prior knowledge; widely cited in systems-security curricula.

### A.3 — Linux seccomp-bpf (2012)

- **Where in the report**: Section 2.1 (third primitive in the capability-based paragraph)
- **Claim it supports**: that kernel-level enforcement primitives for syscall filtering are production-ready
- **Why credible**: in-tree Linux kernel feature; underlies Docker default seccomp profiles and Chrome sandbox.
- **Why this specific primitive**: it's the syscall-filtering primitive that any policy-enforcement layer would build on top of, including any productionised version of our policy generator.
- **In OUR report**: positions kernel-level enforcement as available infrastructure; not a research gap, ours is at the *layer above* (deriving the policy that seccomp-bpf would enforce).
- **Verification**: prior knowledge; documented in Linux kernel `Documentation/userspace-api/seccomp_filter.rst` and widely cited.

### A.4 — AppArmor / SELinux profile families

- **Where in the report**: Section 2.1, capability-based paragraph (rounding-out the existing-tooling enumeration)
- **Claim it supports**: that kernel-level path/syscall/network-host policy enforcement has shipping-quality production tooling
- **Why credible**: both are in major Linux distributions (Ubuntu/Debian use AppArmor; Red Hat / Fedora use SELinux), with decades of deployment.
- **Why these specifically**: they are the two MAC frameworks any reader will know; they make our policy direction concrete by naming downstream consumers.
- **In OUR report**: positions our SKILL.md-derived policy as a candidate input format for either MAC framework.
- **Verification**: prior knowledge; standard distribution components.

---

## B. Sandbox-policy derivation from documentation and observation

### B.1 — `aa-genprof` (AppArmor profile generator) and `audit2allow` (SELinux profile generator)

- **Where in the report**: Section 2.1, sandbox-derivation paragraph (sentence 1)
- **Claim it supports**: that profile generation from runtime observation is an existing tooling pattern
- **Why credible**: standard tools shipped with AppArmor (`aa-genprof`, `aa-logprof`) and SELinux (`audit2allow`) production deployments.
- **Why these specifically**: they are the closest existing analog to our "derive policy from runtime trace" approach. Their input is *runtime audit logs*, our input is *predicted+observed traces* — same direction, different epistemic input.
- **In OUR report**: positions our work as continuing the runtime-observation-based-policy-generation tradition, but with the addition of a *prediction* layer that doesn't require a prior runtime trace.
- **Verification**: prior knowledge; man pages `aa-genprof(8)` and `audit2allow(1)`.

### B.2 — gVisor (Google) and Firecracker (AWS)

- **Where in the report**: Section 2.1, sandbox-derivation paragraph (sentence 2)
- **Claim it supports**: that sandbox primitives at higher isolation levels (VM, syscall-emulation) are mature
- **Why credible**: both run in production at hyperscalers — gVisor underlies Google's sandboxed services, Firecracker is the AWS Lambda / Fargate container runtime.
- **Why these specifically**: they represent the strongest contemporary isolation primitives; useful to name as the eventual deployment target if SKILL.md-derived policies graduated from network-policy (iptables) to full-VM isolation.
- **In OUR report**: scoping context — our policy direction targets `seccomp` / iptables-level enforcement; gVisor / Firecracker are the next-stricter tier if needed.
- **Verification**: prior knowledge; project sites at gvisor.dev and firecracker-microvm.github.io.

### B.3 — Implicit-policy mining from documentation literature (qualified citation)

- **Where in the report**: Section 2.1, sandbox-derivation paragraph (closing sentence)
- **Claim it supports**: that there is an academic tradition of mining policy from documentation, and our work differs in that the input is free-form narrative markdown rather than structured manpages
- **Verification**: I claimed this in the report but **could not confirm a specific Bauer-et-al. citation via WebSearch**. Two paths forward:
  1. Soften the wording in the report: "implicit-policy mining from structured documentation (e.g., manpages, system-call summaries) has prior academic literature; our setting differs in operating on free-form narrative SKILL.md text, which is uncharted." — replaces a specific citation with a general statement of the tradition.
  2. Replace with a verifiable citation: the closest concrete prior work I can verify is Provos & Friedl's "preventing privilege escalation" line of work and the SELinux Reference Policy authoring tradition. Specifically, Smalley et al.'s SELinux Reference Policy (NSA technical reports, 2005-2010) discuss policy authoring from documentation but are not academic peer-review papers.
- **Decision (applied 2026-05-10)**: ✓ DONE. The specific Bauer attribution has been removed from `report.md` §2.1; the surrounding paragraph positions our work in the "policy-from-documentation" direction without a fragile-citation dependency. Verified: `grep -n "Bauer" report.md` returns no matches.

### B.4 — PASSv2: Provenance-Aware Storage Systems (Muniswamy-Reddy et al., USENIX FAST 2009)

- **Where in the report**: Section 2.1, sandbox-derivation paragraph (closing sentence)
- **Claim it supports**: that provenance-based access control has academic prior work distinct from what our work does
- **Why credible**: Harvard SYRAH group's PASS line; Muniswamy-Reddy et al. is FAST 2009; Sigmod 2010 follow-ups. Foundational provenance work in storage.
- **Why this specifically**: it's the most-cited provenance-as-access-control paper; positions our SKILL.md→policy approach as orthogonal to provenance-tracking (which retroactively records what happened) — ours is prospective (predicts what will happen).
- **In OUR report**: dimensional contrast — provenance is "what *did* happen", ours is "what *will* happen given SKILL.md text alone."
- **Verification**: prior knowledge; FAST 2009 program is accessible. Will note as "Muniswamy-Reddy et al." in the verified-citation list.

---

## C. LLM-agent containment & prompt injection — including the two papers Professor Monperrus explicitly named

### C.0a — Liu et al. (2026). "Agent Skills in the Wild: An Empirical Study of Security Vulnerabilities at Scale." arXiv:2601.10338 (January 2026).

- **Where in the report**: Section 1 (Task and approach), Section 2.1 (LLM-agent containment), Abstract — the most heavily-cited single reference.
- **Claim it supports**: that the agentic-skills security problem is real, large-scale, and structurally similar to npm/PyPI supply-chain risk. Also that combined static+LLM detection is the methodologically-favoured approach.
- **Why credible**: First systematic large-scale empirical study of skill-registry security; 42,447 skills collected from two major marketplaces; 31,132 systematically analysed; SkillScan multi-stage detection with 86.7%/82.5% precision/recall; published January 2026 on arXiv with 8 authors. This is the canonical scale-paper Professor Monperrus references in his topic-26 description.
- **Why this specifically**: Professor Monperrus *named this paper explicitly* in the topic-26 description sent to Rayhan. Citing it is non-optional for the report. The complementary-methodology framing (they go broad, we go deep) is the specific positioning we want.
- **In OUR report**: anchors the threat-surface description in Section 1, frames our work as complementary depth analysis on top of their breadth scanning, and provides the empirical baseline that 26.1% of skills are vulnerable — which our deep-instrumentation approach explains the structural causes of.
- **Verification**: WebSearch confirmed arXiv:2601.10338, January 2026 publication, 8 authors led by Yi Liu, the 26.1% / 4-category / 14-pattern numbers, and the SkillScan precision/recall.

### C.0b — Socket (2026). "Socket Brings Supply Chain Security to skills.sh." Socket blog post.

- **Where in the report**: Section 1, Section 2.1, Abstract — second-most-prominent skills-domain citation.
- **Claim it supports**: that the agentic-skills security problem has industrial-scale tooling demand and that a deployed-detector approach is feasible at registry scale.
- **Why credible**: Socket is an established supply-chain-security vendor (Series A funding, well-known in the npm-security community). The blog post documents a deployed scanner over 60,000+ skills.sh entries achieving 94.5% precision / 98.7% recall against known-malicious skills.
- **Why this specifically**: Professor Monperrus *also named this directly* in the topic-26 description. Pairs with Liu et al. to establish the threat-surface motivation: academic empirical study + industrial deployment together.
- **In OUR report**: complements Liu et al. as an industrial-deployment data point for the supply-chain-as-applied-to-skills framing. Sets up our work as complementary depth analysis.
- **Verification**: WebSearch confirmed the Socket blog at socket.dev/blog/socket-brings-supply-chain-security-to-skills, 60,000+ skill catalogue, 94.5%/98.7% precision/recall figures. Socket's coverage of skills.sh integrates with the wider 2026 wave of skill-registry security work (Snyk's ToxicSkills, Orca's research, RedHat developer guidance).

### C.1 — Greshake et al. (2023). "Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection." *AISec '23* (16th ACM Workshop on Artificial Intelligence and Security).

- **Where in the report**: Section 2.1, LLM-agent-containment paragraph (sentence 1); also implicitly grounds Section 5.4 (Findings I+J+K) and Phase 1.C (mutation suite).
- **Claim it supports**: that *indirect prompt injection* — malicious content in retrieved documents subverting an agent — is a recognised threat
- **Why credible**: Authored by Kai Greshake (CISPA), Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, Mario Fritz. AISec '23 is the canonical AI-security workshop co-located with ACM CCS. The paper introduced and taxonomised indirect prompt injection as a class. **167 citations** per Semantic Scholar — establishes it as the seminal work. arXiv:2302.12173.
- **Why this specifically**: it is THE first systematic treatment of the threat surface our adversarial demo (Findings I+J+K) operates in. Without this citation, our adversarial work is unmoored from the literature; with it, our work is positioned as a *variant* (the maintainer is the attacker, not third-party retrieved content).
- **In OUR report**: cited explicitly with the URL `https://arxiv.org/abs/2302.12173`. Explicitly distinguishes our threat-model variant from theirs in the same paragraph.
- **Verification**: WebSearch confirmed the paper's identifier (arXiv:2302.12173), AISec '23 venue, and primary author Greshake. ACM DL link `https://dl.acm.org/doi/10.1145/3605764.3623985`.

### C.2 — Debenedetti et al. (2024). "AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents." *NeurIPS 2024 Datasets and Benchmarks Track*.

- **Where in the report**: Section 2.1, LLM-agent-containment paragraph (sentence 3); also implicitly the closest prior work to our Phase 1.C mutation suite.
- **Claim it supports**: that benchmarking agent attack-defense pairs jointly on utility and security is an established methodology
- **Why credible**: NeurIPS is the top ML venue. The Datasets and Benchmarks Track is the venue for evaluation-protocol contributions. arXiv:2406.13352. Includes **97 realistic agent tasks × 629 security cases**, production-grade benchmark.
- **Why this specifically**: it is the closest published methodology to our Phase 1.C 6-mutation × 4-defense-layer detection-rate table. Our work is smaller-scope (single skill domain, six attack mutations) but methodologically related; positioning helps the reader place our claims.
- **In OUR report**: cited explicitly with `https://arxiv.org/abs/2406.13352`; positions our mutation suite as a smaller-scope methodological cousin.
- **Verification**: WebSearch confirmed NeurIPS 2024 D&B Track venue, arXiv ID 2406.13352, the 97-task / 629-security-case scale, and the AgentDojo project at `agentdojo.spylab.ai`.

---

## D. Supply-chain auditing

### D.1 — OpenSSF Scorecard

- **Where in the report**: Section 2.1, supply-chain paragraph (sentence 1)
- **Claim it supports**: that automated security scoring of open-source repositories is a deployed practice
- **Why credible**: OpenSSF (Open Source Security Foundation) is a Linux Foundation project backed by Google, GitHub, Microsoft, etc. Scorecard is in production use across thousands of repositories.
- **Why this specifically**: the closest existing analog to "automated audit signal for open-source artefact" — establishes that the agentic-skills ecosystem currently lacks an equivalent.
- **In OUR report**: motivates the future-work direction "extend Scorecard-style automated audit to the SKILL.md+bundle artefact class."
- **Verification**: prior knowledge; project at `securityscorecards.dev` and `github.com/ossf/scorecard`. Active maintenance with ~5k GitHub stars.

### D.2 — SLSA (Supply-chain Levels for Software Artifacts), Google 2021

- **Where in the report**: Section 2.1, supply-chain paragraph (sentences 2-3); also Section 2.3 (defense-mapping table) for the binary-fetch-CDN class.
- **Claim it supports**: that supply-chain provenance has a four-level taxonomy (L0-L3) with hermetic-build / signed-provenance requirements at L3
- **Why credible**: introduced by Google 2021, governance moved to OpenSSF, deployed in production at npm / GitHub Actions / Sigstore. v1.1 is the current standard.
- **Why this specifically**: our Finding G's binary-fetch-CDN class (firebase-tools fetching emulator JARs from `release-assets.githubusercontent.com`) is a textbook SLSA-shaped concern. The agent's runtime loads binaries from a separate distribution channel from the npm package, with no provenance check.
- **In OUR report**: cited with URL `https://slsa.dev/`; explicitly noted as the future-work direction for Finding G's binary-fetch class.
- **Verification**: WebSearch confirmed SLSA at slsa.dev, v1.1 with progressive levels L0-L3, the hermetic-build + signed-provenance requirements at L3.

### D.3 — in-toto (Linux Foundation; Torres-Arias et al., USENIX Security 2019 + ongoing standardisation)

- **Where in the report**: Section 2.1, supply-chain paragraph (sentence 4)
- **Claim it supports**: that cryptographically signed pipeline-step attestations are an existing primitive
- **Why credible**: USENIX Security 2019 paper authored by Torres-Arias, Afzali, Kuppusamy, Curtmola, Cappos. Now a Linux Foundation graduated project. Underlies SLSA's attestation format.
- **Why this specifically**: complements SLSA — SLSA gives the *levels* taxonomy, in-toto gives the *attestation format*. Both belong in any supply-chain-audit positioning.
- **In OUR report**: complementary citation alongside SLSA; doesn't carry independent argumentative weight but rounds out the supply-chain literature picture.
- **Verification**: prior knowledge; project at `in-toto.io`.

---

## E. Syscall-level observability

### E.1 — Falco (Sysdig; CNCF graduated)

- **Where in the report**: Section 2.1, syscall-observability paragraph (sentence 1)
- **Claim it supports**: that eBPF-based syscall monitoring is a deployed industrial pattern
- **Why credible**: CNCF graduated project (~7k GitHub stars). Production-deployed across Kubernetes runtimes. Sysdig is a security-vendor with major enterprise customers.
- **Why this specifically**: Falco is the canonical "detect-only" runtime security tool; pairs with Tetragon (detect+enforce) to span the observability tooling spectrum.
- **In OUR report**: positions our `strace` instrumentation as a deliberately-coarser version of the same observability primitive — sufficient for the question this exercise asks, but a Falco-class deployment would scale to per-skill-PR audit in CI.
- **Verification**: WebSearch confirmed Falco's eBPF-based architecture (kernel 4.14+), CNCF status, project at `falco.org`.

### E.2 — Tetragon (Cilium / Isovalent)

- **Where in the report**: Section 2.1, syscall-observability paragraph (sentences 1-2)
- **Claim it supports**: that eBPF-based runtime *enforcement* (kill process, deny syscall) is also deployed in production
- **Why credible**: Built by the Isovalent / Cilium team. Production-deployed in Kubernetes via the Cilium ecosystem.
- **Why this specifically**: complements Falco (detect-only) by adding enforcement; spans the full detect→enforce spectrum that any productionised version of our policy generator would need.
- **In OUR report**: positions Tetragon as the natural future-work deployment platform for the SKILL.md → policy generator output (per-skill PR triggers ephemeral Tetragon-monitored sandbox run).
- **Verification**: WebSearch confirmed Tetragon's eBPF-attached security hooks, kernel-layer enforcement (kill / deny), project at `tetragon.io`.

---

## Summary — credibility matrix

| Citation | Tier | Why included | Verification |
|---|---|---|---|
| Saltzer & Schroeder 1975 | foundational | grounds POLA argument | prior knowledge |
| Watson Capsicum 2010 | systems-security canon | bridges POLA → modern OS | prior knowledge |
| seccomp-bpf 2012 | production primitive | enforcement layer | prior knowledge |
| AppArmor / SELinux | production tooling | downstream MAC framework | prior knowledge |
| aa-genprof / audit2allow | production tooling | runtime-observation policy gen | prior knowledge |
| gVisor / Firecracker | production hypervisors | stricter isolation tier | prior knowledge |
| ~~Bauer et al. policy-by-example~~ | UNVERIFIED | dropped from report | could not confirm |
| PASS / Muniswamy-Reddy 2009 | academic provenance | dimensional contrast | prior knowledge |
| **Liu et al. 2026 "Agent Skills in the Wild"** | **CENTRAL+ — Professor Monperrus named this** | scale of the problem | WebSearch ✅ arxiv:2601.10338 |
| **Socket "skills.sh" 2026** | **CENTRAL+ — Professor Monperrus named this** | industrial deployment | WebSearch ✅ socket.dev |
| **Greshake et al. 2023 AISec** | **central — frames our adversarial work** | seminal indirect-prompt-injection | WebSearch ✅ arxiv:2302.12173 |
| **AgentDojo NeurIPS 2024** | **central — closest related work** | benchmark methodology | WebSearch ✅ arxiv:2406.13352 |
| OSSF Scorecard | production audit | future-work motivation | prior knowledge |
| **SLSA Google 2021** | **central — Finding G future-work** | provenance levels | WebSearch ✅ slsa.dev |
| in-toto | complementary | attestation format | prior knowledge |
| **Falco** | **central — coarser-version-of analog** | eBPF observability | WebSearch ✅ falco.org |
| **Tetragon** | **central — enforcement deployment** | eBPF enforcement | WebSearch ✅ tetragon.io |

**Seven citations are central** (bold) — they ground our most novel claims and were all WebSearch-verified. Two of them (Liu et al., Socket) are explicitly named by Professor Monperrus in the topic-26 description and are now load-bearing for the framing in Section 1, Section 2.1, and the Abstract. Eight are foundational/positioning (prior knowledge, well-known) — they ground the surrounding tradition rather than specific empirical claims. One is dropped from the report due to inability to verify.

---

## ~~Action item~~ — RESOLVED 2026-05-10

The Bauer-et-al. citation has been **removed** from `report.md` §2.1. Final replacement wording (verbatim from the locked report): *"implicit-policy mining from structured documentation (manpages, system-call summaries, machine-readable schemas) and (b) provenance-based access control such as the PASS line of work (Muniswamy-Reddy et al., USENIX FAST 2009) which retroactively records actual behaviour rather than predicting it from text. Our setting is uncharted in two respects: the input is free-form narrative markdown, and the prediction is prospective rather than reconstructive."* — leaves the tradition framed without the fragile-citation dependency.
