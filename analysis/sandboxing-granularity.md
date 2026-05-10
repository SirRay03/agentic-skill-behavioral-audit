# Phase 4.8 — Sandboxing-Granularity Comparison

Professor Monperrus's topic-26 description names *'evaluation of sandboxing approaches at different granularities'*
as a primary subgoal of the hardening direction. This work compares four granularity options
on the network-egress capability axis. The two no-root-required options are tested empirically
(via trace-replay against the granularity rule); the two root-required options are documented
with cost/benefit analysis as future work.

## Granularity options

| Option | Enforcement layer | Root needed? | Bypass-resistance | Per-call overhead |
|---|---|---|---|---|
| **G1** `bwrap --unshare-net` | Linux network namespace | No (user namespaces) | High (kernel-level netns isolation) | One-time at process spawn |
| **G2** Python HTTP proxy + `HTTP_PROXY` env | Application layer | No | Low (CLI must honour `HTTP_PROXY`; many don't) | Per-request |
| **G3** iptables OUTPUT in network namespace | Linux netfilter | **Yes** (CAP_NET_ADMIN) | High | Negligible |
| **G4** seccomp-bpf execve filter | Linux kernel syscall | **Yes** | High | Per-syscall |

## Per-skill granularity replay results

Each row: of the observed skill-attributable hosts, what fraction would be admitted under each
granularity? Higher admit-rate = less restrictive (more legitimate work proceeds, but more
telemetry leakage). Lower = more restrictive (more security, but more false-positive blocks).

| Skill | n_connections (observed) | G1 (unshare-net) | G2 (python-proxy) | G3 (iptables, simulated) | G4 (seccomp, n/a) |
|---|---|---|---|---|---|
| firecrawl-scrape | 4 | 0% | 100% | 100% | n/a (subprocess only) |
| wrangler | 3 | 0% | 100% | 100% | n/a (subprocess only) |
| firebase-hosting-basics | 5 | 0% | 100% | 100% | n/a (subprocess only) |
| agent-browser | 12 | 0% | 17% | 17% | n/a (subprocess only) |

> **Column note**: `n_connections` is the count of observed connect() events (raw connections to skill-attributable hosts), NOT the count of unique hosts. Distinct from the unique-host counts in `failure-mode-taxonomy.md` and `predictor-variance.md`, which deduplicate by FQDN. Multiple connections to the same host inflate the count here (e.g., agent-browser's 12 includes repeated connects to the same Google-services hosts during Chromium's session-bootstrap phase).

## Analysis

**G1 (`bwrap --unshare-net`) admit rate is 0% by definition** — the namespace has no network at
all, so legitimate API calls fail along with telemetry beacons. This is the most-restrictive
granularity and is suitable only for *pure-text/single-output skills* (per Section 5.1's
bimodal cluster). For CLI-wrapping skills it breaks the documented happy path.

**G2 (Python HTTP proxy) admit rate matches G3 (simulated iptables) in our trace-replay** —
both apply the same per-skill allowlist + base-policy union rule. The behavioural difference is
in **bypass-resistance**, not in admit decisions: G2 is application-layer (CLI must honour
HTTP_PROXY), G3 is kernel-layer (CLI cannot bypass). For wrangler — which we know hits
`sparrow.cloudflare.com` regardless of credentials (Finding G) — G2 cannot reliably block
the beacon if the wrangler binary ignores HTTP_PROXY for telemetry calls (which CLIs commonly
do for telemetry). G3 catches it kernel-side regardless.

**G4 (seccomp-bpf execve filter)** doesn't apply to the network-egress axis; it filters
subprocess spawns. For the subprocess capability axis, G4 is the canonical enforcement primitive
(Linux kernel-level, can deny `curl` execution entirely). Our predicted-subprocess data for the
policy generator (Section 6) feeds into G4 directly.

## Empirical bound + recommended composition

The right deployment composes multiple granularities:

- **Per-skill** — G3 iptables with the SKILL.md-derived allowlist + telemetry deny-overlay (Finding M)
- **Per-tool-call** — composed with SKILL.md frontmatter `allowed-tools` (Claude Code already supports this; `gha-security-review` skill in our sample uses it)
- **Per-invocation** — for high-stakes calls like `Bash`-tool invocations within an agent run, deploy a per-invocation seccomp profile (G4) bound to the specific subprocess binaries the agent declared
- **Application-layer fallback** — G2 for environments where root is unavailable; weaker enforcement but better than no enforcement

The conceptual table from Section 6.1 maps each capability type to its appropriate primitive;
this empirical replay shows that the *granularity choice* matters less than the *primitive choice*
(which decides bypass-resistance) — for a given primitive, finer granularity adds overhead but
doesn't change the admit-rate for already-admitted hosts.

## Future-work — what would actually need root

Three concrete deployment paths for the root-required granularities, each with a reasonable
place to surface the privilege:

1. **CI/CD per-PR audit container** (Tetragon or Falco-based runtime observability) — the CI runner is privileged by design; per-skill PRs trigger an isolated container with iptables + seccomp policy from the SKILL.md-derived bundle (Section 6 + Section 6.1).
2. **Skill-marketplace install hook** — skills.sh or the agent-runtime installs the skill into a per-skill privileged container with the policy bundle pre-loaded; the user's host system never grants root to the skill itself.
3. **OS-level privileged daemon** — a small system service that maintains netns + iptables rules on behalf of the agent runtime; the agent-runtime itself is unprivileged, talking to the daemon via a constrained socket.

All three patterns are well-precedented in container security (Docker/runc, Kubernetes admission controllers, Falco operator). The work in this report establishes the *policy content* (what to enforce);
the future work is the deployment plumbing for *where to enforce it*.
