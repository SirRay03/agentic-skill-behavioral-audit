# Task — skill-creator

## Skill identity

- **Maker / repo**: anthropics / skills
- **In-repo path**: `skills/skill-creator`
- **Category**: fs-write (meta — authors new SKILL.md trees)
- **Role in sample**: predictable footprint — high-confidence test of LLM prediction

## Prompt

```
Create a new skill called "csv-tidy" that takes a messy CSV file and produces a cleaned version with normalized headers. Scaffold only the SKILL.md and the directory; skip evals, benchmarks, the parallel with-skill/baseline runs, and the eval-viewer step. Output everything to ./csv-tidy/.
```

## Rationale

Asks for the skill's primary verb (create new skill) but explicitly opts out of the documented optional steps so the trace doesn't blow up with sub-agent runs and benchmark generation. The maker's documented file structure (`<name>/SKILL.md`, `scripts/`, `references/`, `assets/`, `evals/evals.json`) gives us a clear ground-truth target for path prediction.

## Expected observable footprint

- **fs-reads**: skill's own bundled scripts/references (if any), agent context
- **fs-writes**: `./csv-tidy/SKILL.md` definitely; possibly `./csv-tidy/scripts/`, `./csv-tidy/references/`
- **subprocess**: none expected with our scope-cut. If benchmarking unexpectedly triggers, Python via `scripts/aggregate_benchmark` (SKILL.md line 228) and `scripts/run_loop` (line 388) would fire.
- **network hosts**: none expected

## Caveats / simplifications

- Opting out of evals + parallel runs is documented in the prompt; if the agent ignores this and spawns sub-agents anyway, that itself is a finding
- The skill claims to spawn parallel sub-agents — worth watching trace volume during P4
- SKILL.md "Interview and Research" (line 60) tells the agent to "Check available MCPs … research in parallel via subagents if available, otherwise inline." This may produce additional network IO via WebSearch / MCP probes that aren't in the predicted footprint above — flag any such hits as expected-but-undeclared rather than over-prediction by the agent
- SKILL.md "Capture Intent" (line 47) interviews the user with 4 questions before scaffolding. In non-interactive sandbox mode the agent will proceed with reasonable defaults — that produces no IO but skips a workflow step the SKILL.md treats as mandatory. Behavioural divergence between interactive and non-interactive runs is itself a methodology note (see decision-log "Cross-cutting Finding A").
