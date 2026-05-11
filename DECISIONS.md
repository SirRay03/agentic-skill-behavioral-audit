# Design Decisions Log

Chronological record of every non-trivial methodological decision in this project, with rationale and alternatives-considered. Companion to `methodology.md` (which captures the *final* methodology) and `report.md` (which captures the empirical results). Read this if you want to know *why* the work landed where it did.

The full session-by-session research journal is on disk in the working repository; this is the abridged form covering the load-bearing decisions only.

---

## 2026-05-04 — Exercise received

Professor Monperrus emailed the programming exercise: "design and implement a dynamic behavioral auditor for agentic skills". Four numbered tasks (≥10 skills, instrument an agent, LLM-only prediction, qualitative + quantitative comparison) with the explicit invitation to make simplifying assumptions. Treated as a research mini-project, not a graded assignment.

I committed to a Mon 2026-05-11 EOD Stockholm delivery (one week including weekend).

## 2026-05-07 — Sample selection and harness scoping

**Sample design (n=15 + 3 reserves)**: stratified across maker (Anthropic, Microsoft, Cloudflare, Firebase, Vercel Labs, Firecrawl, Browserbase, inference-skills, mattpocock, juliusbrussee), declared category (knowledge-only / fs-write / network / browser-broad / deploy / audit / fs-edit / meta / vague-outlier), and expected gap (tight / medium / large). Selection bias deliberately toward broad-claim skills (≈8) to maximise narrative; 4 controls + 3 in-between.

The full manifest with upstream URLs lives in `manifest.csv`. Every SKILL.md fetched verbatim from `raw.githubusercontent.com` via `gh api -H "Accept: application/vnd.github.raw"`.

**Harness scope decisions**:

- **strace** as the filesystem-syscall capture (`-f -e trace=openat,open,creat,write,unlink,rename,connect`). Considered eBPF (Tetragon/Falco) but rejected for this exercise: heavier setup, still no TLS visibility, and the strace level of detail is sufficient for path/host coverage scoring.
- **tcpdump** for DNS + TCP-SYN. **No TLS interception** — Professor Monperrus's prompt asks about hosts, not URL paths. mitmproxy + cert-injection is the obvious extension and is logged as future work.
- **Sandbox**: original plan was Ubuntu-in-Docker for ephemeral per-skill isolation.
- **Agent**: Claude Code CLI in non-interactive mode (`claude -p`).

**Per-skill task prompts**: authored from each skill's own SKILL.md examples. Three rules — one verb / one minimal target, same prompt across runs, drawn from the maker's own docs (defends against "you cherry-picked a task that triggered side-effects"). Each prompt verified across four review passes for prompt-fidelity, line-citation accuracy, expected fs/network coverage, and reproducibility.

## 2026-05-08 — Pivot: Docker → WSL2-direct

**Decision**: pivot the sandbox from Ubuntu-in-Docker to WSL2 Kali Linux Rolling 2024.4 (kernel 6.6.87.2-microsoft-standard-WSL2) on the Windows 11 host.

**Why**: two compounding constraints made Docker impractical:

1. **No `ANTHROPIC_API_KEY` budget on my side**. The Claude Code subscription I wanted to use authenticates via oauth, scoped to the host environment. Inside an isolated container, the oauth tokens aren't available — I'd need an API key, which means cost.
2. **Docker Desktop not pre-installed**. Setting it up + getting Claude Code working inside containers was an estimated ~8h of yak-shaving on top of the actual exercise.

WSL2 Kali was already configured. Reusing it took ~1h of harness setup (apt-get + npm globals + capability grants for tcpdump) instead of ~8h. Per-skill isolation moves from "ephemeral container" to "fresh `/tmp/work-<skill>/` workdir + `rm -rf` between runs" — coarser isolation, but acceptable for this sample (well-known maker skills, none flagged as malicious by skills.sh's published audits).

**Cost of the pivot**: documented as a deliberate simplification in §7 of the report. A future researcher reproducing this work in a security-sensitive setting (intentionally-malicious skills) should restore Docker.

**Methodology lock**: at this point I locked the predictor at Claude Opus 4.7 `--effort xhigh` and wrote `methodology.md` §6 before any results were observed. Switching headline source after measuring would constitute selection on the dependent variable.

**Default-effort prediction batch was archived**: the first prediction batch ran with default-effort. After the xhigh re-run, the original batch was kept on disk at `skills/<id>/prediction-default.json` as an effort-sensitivity comparison datapoint.

## 2026-05-09 — Tranche 2 expansion (n=15 → n=25)

After running v1 of compare.py on the n=15 baseline, the bimodal F1 pattern was visually clear but n was too small to support a Mann-Whitney significance claim. Decision: add tranche 2 (10 more skills) to broaden maker / category coverage, then re-run.

Tranche-2 makers add Pinecone, Replicate, Prisma, Auth0, Sentry, Semgrep, Vercel-Labs, itsmostafa. Tranche-2 categories add MCP-using, multi-modal, DB-migration, auth-identity, observability, CI-CD-audit, security-audit, Vercel-specific, mobile-native.

**Cost**: ~6h of additional P3 (predict) + P4 (instrument) work; landed by end of day.

## 2026-05-09 — P4 effort locked at `high` (asymmetry with P3 `xhigh`)

The instrumented invocation (P4) consumes meaningfully more tokens than the prediction step (P3): the agent does work, takes multiple tool steps, writes outputs. With the n=25 batch + cross-agent + adversarial + augmented variants on the horizon, locking P4 at `xhigh` would have busted the 5-hour rolling subscription budget.

Decision: lock P4 at `--effort high`. Document the asymmetry in `methodology.md` §6.

**Validation**: a separate Phase 3.N effort-sensitivity probe ran wrangler / semgrep / firebase at three levels (medium / high / xhigh). Mean F1 spread across efforts is 0.170 — smaller than the cross-LLM Jaccard spread of 0.31, so the asymmetry doesn't materially affect headline numbers. Logged at `analysis/stability-effort.md`.

**A from-scratch redo would lock both at xhigh.** Honest acknowledgement of a methodology weakness.

## 2026-05-09 — v3 → v4 agent-infra filter (hosts F1 0.431 → 0.475)

The first compare.py output reported hosts F1 = 0.431 across n=25. Investigation found two sets of agent-runtime endpoints leaking into the "skill-attributable" bucket:

- **Datadog telemetry endpoints** that the Anthropic harness emits independently of any skill. These should be filtered as agent-infra.
- **`downloads.claude.ai`** — Claude Code's plugin auto-update channel, also agent-runtime not skill.

Tightening the agent-infra filter (`analysis/compare.py` v4) bumped hosts F1 from **0.431 to 0.475**. Older v1, v3 outputs archived at `analysis/archive-2026-05-09-v*` for chronology.

**Note (revised 2026-05-11 post-review)**: this entry initially treated 0.431 as a purely historical (pre-v4-filter) value. That framing was imprecise. The v4 filter bumped the **aug-inclusive** sample (25 production + 3 Finding L aug variants, n=9) from 0.431 to 0.475. The **production-only** sample under the v4 filter is also 0.431 (n=6 — see `analysis/predictor-vs-truth.md`); the two 0.431 values coincide numerically but refer to different filtered samples. After the post-review pass, the report now leads with the production-only **0.431** as headline and labels 0.475 explicitly as the aug-inclusive value. Both numbers are correct; previous wording suggested 0.431 was no longer current, which is not true.

## 2026-05-09 — Scope expansion (Phase 6)

The n=25 baseline finished with F1 numbers in hand. The remaining time budget (Sat–Mon) was tight but non-zero. Decision: scope-expand instead of leaving slack on the table. Each enrichment fed empirical evidence back into the headline findings:

1. **Cross-agent control under Codex CLI** (n=7 skills). Tests whether the headline gaps reproduce across agent harnesses or are Claude-Code-specific instrumentation artifacts. Confirmed reproduction (Findings G + A reshaped).
2. **Synthetic adversarial demo + 6 attack-pattern mutations** (Phase 1.C). Tests whether the predictor + runtime catch a maintainer-as-attacker SKILL.md.
3. **Augmented-SKILL.md inverse experiment** (Phase 3 / Finding L). Three worst-F1 CLI-wrappers re-prompted with explicit "Observed Runtime Endpoints" section. Largest lift: firebase-hosting-basics +25pp.
4. **Real-creds variants** (3 skills). Empirical anchor for the Limits-section claim that stub-creds runs are a strict lower bound on observed network surface.
5. **Static regex baseline** vs LLM predictor recall. Headline 2.5× ratio.
6. **SKILL.md → policy generator + retroactive evaluation**. The constructive answer to Professor Monperrus's research question.
7. **Predictor-variance batch** (full n=25 under fresh-Claude + Codex). Establishes the LLM-of-prediction as a load-bearing methodological parameter (Finding N).

## 2026-05-09 — `belt` CLI 404 / web-search self-correction

`setup-skills.sh` initially tried to install `@inference-sh/cli`, the package name documented in the web-search SKILL.md. `npm install` returned 404 on `registry.npmjs.org`. The agent at runtime self-corrected by installing `@inferencesh/belt` (the actual maintained package).

What this taught the work: a per-skill mid-execution package-name correction is exactly the kind of supply-chain risk the audit is designed to surface. Logged as a borderline category-4 (supply-chain) instance in the final §5.7 cross-classification against Liu et al.'s taxonomy.

## 2026-05-09 — Browser-spawning skills + orphan Chrome

P4 runs of `agent-browser` and `cookie-sync` exited cleanly but left Chrome processes alive — which blocked `strace`'s wait-for-children indefinitely, hanging the run.

**Fix**: wrapped `strace` invocations in `timeout --kill-after=30 900` (15-minute hard cap, 30-second `SIGKILL` follow-up) and added `pkill -KILL -f "agent-browser-chrome-"` post-run cleanup.

**Cost**: two runs lost ~12 minutes each before the timeout was added; both re-ran successfully after.

## 2026-05-10 — L1 mutation-suite correction (100% → 83%)

An early draft of the brittleness ablation reported L1 (static regex) catching 6/6 mutations. Investigation traced the inflation to `mutation-suite.py` and `mutation-suite-ablation.py` using `rglob("*.md")` to find SKILL.md text — which inadvertently scanned each mutation directory's `task.md` fixture file alongside the actual SKILL.md. The task.md fixtures contain the attack-target string (`attacker.example.com`) as part of the prompt setup, so the `attacker-literal` regex was triggering on fixture content rather than SKILL.md content.

**Fix**: added `NON_BUNDLE = {"task.md", "task.md.bak"}` exclusion in both scripts. **Honest result**: L1 catches 5/6 (the M1 obfuscated-curl mutation evades all regex regimes via env-var-assembly).

**Why this matters**: the corrected 83% is the headline used everywhere in the final report. The 100% figure exists only as a historical chronology note in `analysis/mutation-suite-ablation.md`. The brittleness story is the *honest* version: under realistic minimal regex (R3 — sudo / rm -rf / pipe-to-shell only) detection drops to **0%**.

## 2026-05-10 — Codex `/tmp` HOME constraint

The clean-home Codex predictor batch (Section 5.5 / Finding N) initially failed because Codex 0.129.0 refuses to create helper binaries when `CODEX_HOME` is under `/tmp`.

**Workaround**: `harness/codex-one-off.py` uses the system home for codex auth state but writes outputs to `/tmp/fresh-predictor-batch/`. Predictor variance results unaffected; only the directory layout for the predictor batch had to change.

## 2026-05-10 — 256× cross-agent write inflation reframed

The Codex-vs-Claude wrangler comparison initially showed Codex producing 2556 writes vs Claude's 10 — a 256× ratio. Initial reading: "Codex over-scaffolds the wrangler task."

**Phase 2.J mechanism investigation** (`analysis/mechanism-investigation.md`) decomposed the 2556 writes by path prefix and found 2541 of them were Codex's plugin-marketplace manifest tree — ~117 vendor product structures extracted to a tempfs-backed location during agent startup, then cleaned up before run completion.

After filtering `plugins/*` and `~/.codex/*` (per-agent bootstrap cost), Codex's task-attributable writes dropped to 9. Roughly 1:1 with Claude.

**The methodologically interesting finding** is therefore not "Codex over-scaffolds" but rather **"syscall-trace cross-agent footprint comparisons are dominated by per-agent bootstrap costs, not per-task behaviour"**. Reported as Finding H with the mechanism investigation as the supporting analysis.

## 2026-05-10 — Professor Monperrus-alignment passes

Reread Professor Monperrus's topic-26 description and the two named references: [Liu et al. (2026) "Agent Skills in the Wild"](https://arxiv.org/abs/2601.10338) (n=42,447, 26.1% vulnerable) and [Socket's deployed skills.sh scanner](https://socket.dev/blog/socket-brings-supply-chain-security-to-skills) (60,000+ skills, 94.5%/98.7% precision/recall). Earlier drafts of the report didn't reference either; the topic-26 framing "capability-based permission models / sandboxing granularities / static + semantic detection" was implicit but not verbatim.

**Decision**: rewrite §1, §2.1, §5.7, §6.1, §8 to anchor explicitly to Professor Monperrus's named subgoals and references. Add a brittleness-on-obfuscation ablation (`analysis/mutation-suite-ablation.md`) to empirically validate Professor Monperrus's brittleness claim. Add capability-vocabulary table at §6.1 with enforcement-primitive granularity options. Add cross-classification of our findings against Liu et al.'s 4-category vulnerability taxonomy.

**Output of this pass**: report.md grew from ~10 to ~14 PDF pages; the abstract, §1, §2.1, §5.7 cross-classification, §6.1 capability vocabulary, and §8's three-subgoal mapping all became explicit topic-26 anchors.

## 2026-05-11 — Submission

Final report `report.md` + companion artefacts (`EXECUTIVE_SUMMARY.md`, `SKILL_AUTHORING_GUIDE.md`, the pip-installable `skill-auditor` CLI, the `skill-policy.json` bundle prototype, and the dashboard-in-progress) submitted to Professor Monperrus by EOD Stockholm.

Future-work follow-up sequenced in §8: cross-agent on full 25 (currently n=7), TLS interception via mitmproxy, live iptables-in-netns enforcement deployment, predictor extensions for L2 misses (M4 bundled-sibling, M6 dependency-confusion), Tetragon/Falco runtime observability for CI integration, and replication on intentionally-malicious skills.
