# skill-auditor

Behavioural audit toolkit for agentic skills. Derives sandbox policy from `SKILL.md` text via LLM extraction, and verifies against runtime traces captured under instrumented invocation.

This package is the deployable distillation of the empirical work shipped at the repository root — the n=25 audit, mutation suite, and SKILL.md → policy direction documented in `../report.md`.

## Install

```bash
pip install -e .
# or with stats + viz extras
pip install -e ".[all]"
```

## Subcommands

```
skill-auditor predict <SKILL.md> [--predictor claude|codex] [--effort xhigh|high|medium|low]
                              # Emit prediction.json (LLM-extracted IO surface)

skill-auditor audit   <SKILL.md> [--task PROMPT] [--out DIR]
                              # Full P3 (predict) + P4 (instrumented strace + tcpdump run);
                              # emits prediction.json + trace.json into <out>/

skill-auditor policy  <SKILL.md> [--prediction PATH] [--trace PATH] [--out PATH]
                              # Emit skill-policy.json (capability bundle: hosts allowlist
                              # with wildcard deflation, telemetry deny-overlay, maintainer
                              # trust hint)
```

## What this is for

Three deployment paths the report's Section 8 + 6.1 motivate:

1. **Per-PR audit in CI** — `skill-auditor audit` on each skill PR, posting the prediction-vs-observed delta as a reviewer comment.
2. **Skill-marketplace install hook** — `skill-auditor policy` runs at install time and emits a `skill-policy.json` companion artefact loaded alongside the SKILL.md by the agent runtime.
3. **Local researcher use** — single-command reproduction of the n=25 methodology against any new SKILL.md.

## Limitations

- `audit` requires `strace`, `tcpdump`, and a Claude Code or Codex CLI on `PATH` — Linux/WSL only.
- `predict` and `policy` work cross-platform.
- Predictor identity matters (cross-LLM Jaccard 0.41–0.43 on hosts between Claude Opus 4.7 and OpenAI Codex; see `report.md` §5.5).
- The harness simplifications carry over: single-representative-invocation, no TLS interception, no MCP-mediated traffic capture.

## Provenance

This package is research code from a 4-month evaluation exercise, not a production-hardened audit tool. Liu et al. and Socket's deployed scanners are the broad-detection complement at registry scale; this is the depth-instrumentation companion.
