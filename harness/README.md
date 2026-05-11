# Harness

Behavioural-auditor harness for P2/P3/P4. Run from inside WSL2 kali (or any Linux environment with `strace` + `tcpdump`). Scripts compute paths relative to their own location, so the project can live anywhere; clone the repo and `bash harness/...` works directly.

## Files

| File | Purpose |
|---|---|
| `setup-skills.sh` | One-time: install all 25 skills under `~/.claude/skills/<id>/`, plus per-skill CLIs (firecrawl, wrangler, firebase-tools, agent-browser, belt) into `~/.npm-global` |
| `extract-prompt.py` | Parse `## Prompt` code block out of `skills/<id>/task.md` |
| `predict.py` | P3: feed each `skills/<id>/SKILL.md` to claude, write `skills/<id>/prediction.json` |
| `run-skill.sh` | P4 single skill: tcpdump + strace around `claude -p "<prompt>"`. Outputs `skills/<id>/raw/*` and `skills/<id>/trace.json` |
| `parse-strace.py` | Parse `syscalls.log` → `{paths_read, paths_written, paths_deleted, connects}` |
| `parse-pcap.py` | Parse `net.pcap` → `{dns_queries, tcp_destinations}` (uses scapy) |
| `run-all.sh` | P4 all-25 driver. `run-all.sh --only <skill>` for the validation gate |
| `workspaces/<skill>/` | Pre-seeded fixtures for skills whose task references files we need to provide (e.g., `improve-codebase-architecture/mini-repo/getUser.ts`) |

## Order of operations

1. `bash harness/setup-skills.sh` — installs skills + CLIs (~5–10 min, network-heavy)
2. `python3 harness/predict.py` — P3 predictions for all 25 (~5–15 min total, claude API time)
3. `bash harness/run-all.sh --only web-search` — validation gate. Verify trace.json has fs + net data.
4. `bash harness/run-all.sh --continue-on-error` — P4 main batch. Sequential, logs to `harness/run-all.log`.
5. P5 analysis lives elsewhere (`analysis/`).

## Outputs per skill

```
skills/<id>/
├── SKILL.md              # already there from earlier — verbatim from upstream
├── task.md               # already there — task prompt + rationale + expected footprint
├── prediction.json       # P3 output: LLM's prediction from SKILL.md alone
├── trace.json            # P4 output: combined fs + net observed footprint
└── raw/
    ├── syscalls.log      # raw strace output
    ├── net.pcap          # raw tcpdump capture
    ├── claude-stdout.json
    ├── claude-stderr.log
    ├── tcpdump.log
    ├── fs-trace.json     # parsed fs subset
    └── net-trace.json    # parsed net subset
```

## Limits / known gotchas

- **Trace blind spots**: see `methodology.md §11`. WebSearch / WebFetch / Agent (subagent) tool calls inside Claude Code go through the Anthropic harness and do NOT appear in our strace/tcpdump.
- **Cloud-credential-gated skills**: firebase-hosting-basics, wrangler, azure-validate run with empty creds — captured up to auth-failure point.
- **agent-browser self-discovery**: SKILL.md mandates `agent-browser skills get core` before any verb. Expect that subprocess + likely network call in the trace.
- **Subscription rate limits**: Claude Code Max has a weekly token budget. If we hit it mid-P4, batch across the reset window.
