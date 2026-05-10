# Phase 2.J — Mechanism investigation

Two unanswered "why" questions from the existing data are answered here.

## J.1 Why does Codex produce 256× more writes than Claude on wrangler?

### Original observation (Finding H)

In Section 5.3 of the report we noted that on the same wrangler task, Claude Code produced 10 skill-attributable writes while Codex CLI produced 2556 — a 256× ratio. Initial reading: "Codex over-interpreted the prompt and scaffolded its own plugin around wrangler."

### What the trace actually says

Categorising Codex's 2662 writes from `skills/wrangler/trace-codex.json` by path prefix:

| Category | Count | Notes |
|---|---|---|
| `plugins/<vendor>/...` (relative path) | **2541** | The vast majority — see breakdown below |
| `~/.codex/` agent-state writes | 104 | OAuth state, session DB, cache files |
| `.agents/skills/plugin-creator/...` (relative) | 5 | The previously-flagged "plugin scaffolding" |
| `/tmp/work-codex-wrangler/worker/...` | 4 | The actual wrangler.jsonc + src/index.ts + deploy bundle |
| `~/.config/codex/...` | 2 | Codex config files |
| `/dev/tty`, `/dev/null` | 2 | TTY |
| Misc | 4 | npm cache, scratch files |

**The bulk (2541) are not writes the agent made on behalf of the wrangler task.** They are Codex's plugin-marketplace manifest tree, visible in the syscall trace at agent startup time.

### Top-level breakdown of `plugins/...` writes

| `plugins/<vendor>/` | n writes | What it is |
|---|---|---|
| cloudflare | 366 | Codex's Cloudflare apps/skills bundle (matches our task domain coincidentally) |
| life-science-research | 163 | Domain-bundled plugin |
| build-web-apps | 138 | Web-framework plugin |
| vercel | 125 | Vercel apps |
| twilio-developer-kit | 115 | Twilio apps |
| figma | 94 | Figma apps |
| notion | 86 | Notion apps |
| hugging-face | 83 | HF apps |
| netlify | 74 | Netlify apps |
| (~115 more vendors at 3-72 writes each) | ~1300 | Codex's full app marketplace |

The directory tree per vendor includes: `.app.json`, `.codex-plugin/plugin.json`, `assets/app-icon.png`, `agents/openai.yaml`, plus optional `skills/<verb>/SKILL.md`, `skills/<verb>/agents/openai.yaml`, `skills/<verb>/references/*.md`, `skills/<verb>/scripts/*.py`. This is **the Codex 0.129.0 product structure**, not an artifact of the wrangler task.

### Why these writes don't survive on disk

After the run, `/tmp/work-codex-wrangler/` contains *only* `worker/` (the actual task output). The plugins/ tree does not exist on disk. Hypothesis: Codex extracts its plugin manifest cache to a tempfs-backed location during startup, the writes are visible to `strace -e trace=write`, and the location is cleaned up before the run completes. Alternative hypothesis: the writes go to memory-mapped files that strace records as `write` syscalls but the underlying inodes never persist past the process lifetime.

### Revised Finding H

**The 256× ratio is dominated by Codex's plugin-marketplace bootstrap cost, not by skill-task behavior.** Re-running the comparison after filtering `plugins/*` and `~/.codex/*` paths:

- Claude Code skill-attributable writes: 10 (unchanged)
- Codex skill-attributable writes (post-filter): **9** (4 wrangler workdir + 5 `.agents/skills/plugin-creator/` scaffolding + 0 home-state)

So the **task-attributable** ratio is roughly **1:1** — both agents do approximately the same amount of work on the same task. The original 256× number is **a measurement artifact of Codex's startup phase being syscall-visible while Claude's skills system is harness-routed**.

This is a *different and arguably more interesting* finding than the original framing. The methodological lesson: when comparing strace-visible footprints across agent harnesses, the agents' own startup-time bootstrap costs dominate any task-specific differences. A clean per-(skill, agent) comparison requires per-agent baseline subtraction (run the agent with an empty prompt, capture the bootstrap footprint, subtract from the task run).

### Implication for the report

Section 5.3's headline claim ("Codex 256× more writes than Claude") needs updating. Two possible revisions:

1. **Honest correction**: present the 256× as the *raw* number and the ~1× post-filter number, framing the finding as "the syscall-layer footprint is dominated by per-agent bootstrap, not per-task work — a methodology caution against naive cross-agent footprint claims."

2. **Stronger finding**: keep the 256× as raw observation, add this mechanism investigation as the *explanation*, and reframe Finding H as: **"agent-specific syscall-layer footprints can differ by orders of magnitude on identical tasks, and the difference is not task-attributable; cross-agent policy generation must subtract per-agent baselines or operate at a layer above syscalls."**

Recommendation: option 2. The original 256× number is empirically real; the *interpretation* is what the mechanism work corrects.

## J.2 Why do both agents skip `developers.cloudflare.com` despite SKILL.md mandate?

### Original observation (Finding A reshaped, Section 5.2)

Both Claude Code and Codex CLI on the wrangler task ignored SKILL.md's third-sentence directive *"Prefer retrieval over pre-training"* — neither hit `developers.cloudflare.com` for the documented retrieval. Section 5.2 framed this as an *agentic, not architectural* failure mode: both agents elected pre-training over retrieval despite different harness routing.

### Hypothesis

The retrieval-skip happens because both agents' pre-training data already contains wrangler conventions sufficient to write a minimal Worker. The retrieval mandate is honoured *only when the model lacks the knowledge to act* — for well-documented widely-used CLIs like wrangler, the pre-training is sufficient and the mandate is silently ignored.

### What evidence we have

Three runs (Claude Code stub-creds, Claude Code real-creds, Codex stub-creds) on the same task all skip `developers.cloudflare.com`. The agent's own self-reported reasoning is not in our trace data (the agent's tool-call history is invisible to syscall instrumentation — Finding A blind spot). We can observe *that* the retrieval is skipped; we cannot observe *why* without an interpretability probe.

### What would settle the question

A direct probe: run the same task on a less well-known CLI tool whose conventions are NOT in the model's pre-training (e.g., a tool published less than three months before the model's training cutoff). If retrieval *is* honoured for that tool but not for wrangler, the pre-training-sufficiency hypothesis is supported. If retrieval is skipped regardless, the hypothesis fails and a different mechanism is at work (e.g., the agents systematically deprioritise SKILL.md retrieval mandates as a class).

This probe is out of scope for the current submission window but is a natural Phase 3 / future-work follow-up.

### Implication for the report

Section 5.2's Finding A reshaped framing is correct as far as the data go. The mechanism is not yet established — replace "agents *elect* pre-training" with "agents *appear to elect* pre-training based on the cross-agent reproduction; the underlying mechanism (pre-training-sufficiency vs. systematic deprioritisation) is a future-work probe."

## Summary

Both mechanism investigations strengthen the report:

- **J.1** — the headline 256× write inflation is real but interpretable: it's per-agent bootstrap-cost artifact, not per-task scaffolding inflation. **Methodology lesson**: cross-agent syscall-trace comparisons require per-agent baseline subtraction.
- **J.2** — the cross-agent retrieval-skip is empirically reproducible (n=3) but mechanistically unconfirmed. The pre-training-sufficiency hypothesis is the most parsimonious explanation; settling it requires a Phase 3 probe with a less-canonical CLI.
