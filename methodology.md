# Methodology

> Synthesised methodology spine for the final submission. Records the design decisions actually applied to the n=25 sample, post-pivot to WSL2 and post-tranche-2 scope expansion. For the chronological version with rationale and alternatives-considered, see `DECISIONS.md`. For the final empirical results, see `report.md` and `analysis/stats.md`.

## 1. Problem statement

Professor Monperrus (KTH ASSERT) sent the exercise on 2026-05-04 in the context of his research topic *"Automatic Hardening of Agentic Skills"*. The verbatim prompt is in `README.md`.

Our reading: the exercise measures **whether a skill's declared markdown contract honestly describes its runtime behavioural footprint**. The implicit research framing is that if the declared-vs-observed gap is small, sandbox policies can be derived from skill markdown alone (least-privilege from documentation); if the gap is large, dynamic auditing is mandatory. Either result is a usable empirical foundation for the hardening direction.

A subtle but load-bearing methodological point: many "skills" are pure instructional prose. The skill itself does no IO — the *agent* acting under the skill's behavioural prior does the IO. We therefore measure **the capability footprint of an agent-with-skill on a representative task**, not the skill's intrinsic ops. We acknowledge this in the report and run zero-IO control skills (`grill-me`, `caveman`) to anchor the distinction.

## 2. Sample design

- **n = 25** production skills (tranche 1 = 15 fetched 2026-05-07, tranche 2 = 10 added 2026-05-09 to broaden maker / category coverage), **+1 synthetic adversarial demo** (`zz-adversarial-summarize-text`), **+6 attack-pattern mutations** of the adversarial demo (`zz-mutation-{1..6}-*`), **+3 augmented-SKILL.md variants** (`*-aug` for the three worst-F1 CLI-wrappers — Finding L inverse-experiment).
- Stratified across maker (Anthropic / Microsoft / Cloudflare / Firebase / Vercel Labs / Firecrawl / Browserbase / Pinecone / Replicate / Prisma / Auth0 / Sentry / Semgrep / inference-skills / mattpocock / juliusbrussee / itsmostafa) and declared category (knowledge-only / fs-write / network / browser-broad / deploy / audit / fs-edit / meta / vague-outlier / MCP-using / multi-modal / DB-migration / auth-identity / observability / CI-CD-audit / security-audit / Vercel-specific / mobile-native).
- Selection bias deliberately toward broad-claim skills (≈12) to maximise narrative; 5 controls + 8 in-between for stratification.
- One Snyk-flagged skill (`azure-validate`) included as anomaly anchor that ties our work to existing static audits at skills.sh.

The full list lives in `manifest.csv`. Each row's task prompt and expected observable surface live in `skills/<id>/task.md`.

## 3. Pipeline (P0–P6, final)

| Phase | Final status | Output |
|---|---|---|
| P0 — Scope and design | done | `methodology.md`; harness design pivoted Docker → WSL2-direct on 2026-05-08 (see `DECISIONS.md`) |
| P1 — Per-skill task prompts | done (n=25) | `skills/<id>/task.md` × 25, verified across 4 review passes |
| P2 — Harness build | done | `harness/` scripts + workspace fixture; validation gate passed on `frontend-design`; orphan-Chrome `pkill` cleanup added for browser-spawning skills |
| P3 — LLM prediction (Claude Opus 4.7 xhigh) | done (n=25) | `skills/<id>/prediction.json`; archived `prediction-default.json` for the early default-effort baseline |
| P4 — Instrumented invocations (Claude Code, `--effort high`) | done (n=25) | `skills/<id>/trace.json` |
| P5 — Compare and write | done | `analysis/compare.py` (v4 agent-infra filter); aggregate F1 in `analysis/summary.md` and `analysis/stats.md` (paths_read 0.368, paths_written 0.375, **hosts 0.431** production-only / 0.475 [0.399, 0.542] aug-inclusive — see `analysis/predictor-vs-truth.md` for the production-only n=6 and `analysis/stats.md` for the n=9 aug-inclusive sample) |
| P6 — Scope expansion | done | Cross-agent control under Codex on n=7; adversarial demo + 6-mutation suite; augmented-SKILL.md inverse experiment (3 skills); real-creds variants (3 skills); static regex baseline; predictor-variance batch (fresh-Claude + Codex predictions on full n=25); SKILL.md → policy generator + retroactive evaluation; brittleness ablation; sandboxing-granularity comparison; pip-installable `skill-auditor` CLI; registry-deployable `skill-policy.json` bundle prototype (5 generated examples) |

## 4. Harness

- **Agent**: Claude Code CLI in non-interactive mode (`claude -p "<task>" --dangerously-skip-permissions`). Authenticated via the user's existing Claude Code subscription (oauth, no API key), so token cost is $0.
- **Sandbox**: WSL2 Kali Linux Rolling 2024.4 (kernel 6.6.87.2) on a Windows 11 host. Originally planned as Ubuntu-in-Docker, **pivoted to WSL2-direct** (see `DECISIONS.md` "Pivot: Docker → WSL2-direct") due to (a) absence of `ANTHROPIC_API_KEY` budget on the user side, and (b) Docker Desktop not pre-installed. WSL2 already had a working kali distro; reusing it saves ~30–45 min of install time and keeps cost at $0. Trade-off: per-skill isolation is via fresh `/tmp/work-<skill>/` workdirs and `rm -rf` between runs rather than ephemeral containers. Acceptable for this sample (well-known maker skills, not malware) and documented in the Limits section.
- **Filesystem capture**: `strace -f -e trace=openat,open,creat,write,unlink,rename,connect -s 256` produces structured JSON of paths read / written / deleted, plus connect destinations. Runs as the `sirray` user, no sudo needed.
- **Network capture**: `tcpdump` capturing DNS queries (port 53) and TCP-SYN packets. **No TLS interception** — Professor Monperrus's prompt asks about hosts, not URL paths. tcpdump runs without sudo via `cap_net_raw,cap_net_admin+eip` capability granted once at setup time.
- **Skill installation**: pre-installed under `~/.claude/skills/<id>/` at harness setup time, so install-time IO does not contaminate the trace.
- **Cloud-credential-gated skills** (`firebase-hosting-basics`, `wrangler`, `azure-validate`) run with empty/stub creds. Captured footprint is treated as a lower bound and flagged in the report's Limits section.
- **Validation gate**: harness must produce a clean trace on `web-search` (smallest expected surface) before scaling to all 25 runs. If validation fails, stop and fix.
- **Subscription rate limits**: Claude Code subscription has 5-hour rolling token budgets. P4 batches were paced across multiple windows where needed. Flagged as a known constraint, not a blocker.

## 5. Per-skill invocation prompts

Authored from each skill's own SKILL.md examples. Three rules:

1. One verb, one minimal target — no compound asks
2. Same prompt across runs — reproducible
3. Drawn from the maker's own documentation — defends against "you cherry-picked a task that triggered side-effects"

The prompts live in `skills/<id>/task.md`. **Status**: each tranche-1 prompt verified against the verbatim SKILL.md across four review passes (initial verification, second-pass tightenings, third-pass cold-read against the upstream maker docs, fourth-pass cross-cutting synthesis); tranche-2 prompts authored 2026-05-09 against the same conventions. Five task.md files were revised across the passes; the original five cross-cutting findings (A–E) grew to fifteen (A–O) over the scope-expansion phase. See `DECISIONS.md` for the chronology.

## 6. LLM prediction step

- **Input**: the verbatim `SKILL.md` text only. No bundled `*.md` siblings, no README, no install command — only what the maker uploaded as the canonical contract. Matches Professor Monperrus's wording "skill's markdown text alone".
- **Model**: Claude Opus 4.7 (1M context). Used consistently across all 25 skills via the host-side Claude Code subscription. Two additional predictor sources were run on the same n=25 for cross-LLM variance analysis (Section 5.5 / Finding N): fresh-Claude (clean `$HOME`, no project context) and OpenAI Codex CLI; outputs land at `skills/<id>/prediction-fresh.json` and `skills/<id>/prediction-codex.json` respectively.
- **Effort level**: `--effort xhigh` for the P3 prediction step (locked 2026-05-08). The first prediction batch ran with default-effort and was archived to `skills/<id>/prediction-default.json`; the canonical `skills/<id>/prediction.json` is the xhigh re-run. Locking xhigh ensures reproducibility and gives the predictor enough thinking budget to handle multi-step / referential skills (e.g., `skill-creator`, `improve-codebase-architecture`, `wrangler`) without rationale truncation. The default-effort archives remain on disk as a small effort-sensitivity comparison data point for the report's reflection section. **Note**: P4 (instrumented invocation) uses `--effort high`, not xhigh — see `DECISIONS.md` entry 2026-05-09 "P4 effort locked" for the rationale behind the asymmetry.
- **Prompt schema**: structured JSON output:
  ```json
  {
    "paths_read": ["string predicates, e.g. /etc/hosts or ~/.config/*"],
    "paths_written": ["string predicates"],
    "paths_deleted": ["string predicates"],
    "hosts": ["FQDN or domain suffix"],
    "subprocesses": ["binary names"],
    "rationale": "free-form 2-4 sentences"
  }
  ```
- **Per-skill prediction file**: `skills/<id>/prediction.json`

## 7. Comparison metrics

- **Set-based**: precision, recall, F1 over predicted-vs-observed paths and hosts; Jaccard similarity per skill.
- **Path comparison**: canonicalised by prefix and predicate match (`/etc/hosts` matches `/etc/hosts`; `/tmp/*` matches `/tmp/foo123`). Predictions phrased as predicates.
- **Host comparison**: FQDN suffix match (`api.firecrawl.dev` matches a `*.firecrawl.dev` predicate).
- **Aggregate**: mean / median per-skill F1, with stratification by maker and category.
- **Qualitative**: 3 deep-dive cases — one tight match, one over-prediction, one under-prediction. Showcase pattern, not just numbers.

## 8. Acknowledged simplifications (verbatim in report's Limits)

| Simplification | Why okay | Cost |
|---|---|---|
| TLS not decrypted | Exercise asks hosts, not URLs | No URL-path comparison |
| `strace` opens/connects only | Sufficient to identify paths + hosts | Misses mmap-only IO |
| One representative invocation per skill | Professor Monperrus's wording | No multi-task fuzzing |
| Stub creds for cloud skills | Provisioning out of scope | Post-auth branches unobserved |
| Single agent (Claude Code) | Professor Monperrus: "agent of your choice" | No cross-agent comparison |
| Single LLM for prediction | Cost and consistency | No cross-LLM variance |
| SKILL.md only as prediction input | Professor Monperrus's wording | Bundled extras inform agent but not predictor |

## 9. Risks and off-ramps

- **Harness build overruns 10h**: drop n from 15 → 12 (kill `firebase-security-rules-auditor`, `cookie-sync`, `caveman`); reclaim ~2h.
- **Specific skill won't run sandboxed**: substitute from reserve list (`triage`, `appinsights-instrumentation`, `safe-browser`).
- **Trace format unparseable for an edge case**: document as "no clean trace; excluded from quantitative section, mentioned qualitatively". Don't fight it.
- **LLM prediction returns malformed JSON**: re-prompt once; if still bad, fall back to free-form parsed by hand. Document in Limits.

## 10. Deliverable

Short report (4–6 pages PDF) + this repo. Sent to Professor Monperrus by **Mon 2026-05-11 EOD Stockholm**.

## 11. Trace blind spots

The harness captures syscall- and network-level activity inside the sandboxed container only. Several classes of IO are systematically invisible. We disclose them up front so the comparison numbers are read correctly.

- **TLS payloads** — `tcpdump` captures hosts and ports, not URL paths or request bodies. Out of scope for this exercise (Professor Monperrus asks hosts).
- **Agent-tool-mediated IO** — Claude Code's first-class tools (`WebSearch`, `WebFetch`, `Agent`/subagent dispatch) execute via the Anthropic harness, not via subprocesses inside our sandbox. These calls do not appear in `strace` or `tcpdump`. Affects skills whose SKILL.md mandates retrieval (e.g., `wrangler` lines 16-18 — *"Prefer retrieval over pre-training"*) or subagent use (e.g., `improve-codebase-architecture` line 37 — *"use the Agent tool with subagent_type=Explore"*; `skill-creator` parallel with-skill/baseline test runs).
- **Async / post-task callbacks** — telemetry beacons fired after the agent returns, queued background tasks. Not captured.
- **mmap-only IO** — rare in agent workflows but invisible to `strace`'s `open`/`read`/`write` filter.

**Implication for comparison**: predicted IO that maps to a blind spot is tagged `unobservable` rather than counted as a false-positive prediction. The quantitative section reports two precision/recall pairs per skill — one against directly-observed IO, one with `unobservable` predictions excluded — so the reader can see where the measurement gap matters. See `DECISIONS.md` "Cross-cutting Finding A" for the full classification.
