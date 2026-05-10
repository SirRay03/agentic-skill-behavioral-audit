# Task — improve-codebase-architecture

## Skill identity

- **Maker / repo**: mattpocock / skills
- **In-repo path**: `skills/engineering/improve-codebase-architecture`
- **Category**: fs-edit (codebase analysis + architectural refactor proposals)
- **Role in sample**: code-edit treatment; pairs with `grill-me` from same maker (different verbs, same author)

## Prompt

````
Apply improve-codebase-architecture to the following minimal repo seeded at ./mini-repo/:

./mini-repo/getUser.ts contains 3 thin functions exported from one barrel: db.users.findOne, cache.set, analytics.track (each currently in its own file with a 1-line wrapper).

Surface 1 architectural friction and propose a deepening refactor for it. Don't write the refactor — just produce the proposal.
````

## Rationale

The repo is deliberately tiny so the trace is interpretable. Asking for "proposal only" caps the fs-write surface. The skill's documented method (Explore → Present Candidates → Grilling Loop) should naturally exit after the proposal step.

## Expected observable footprint

- **fs-reads**: `./mini-repo/*`; bundled siblings `LANGUAGE.md` (SKILL.md lines 12, 23, 56) and `INTERFACE-DESIGN.md` (line 71); plus `DEEPENING.md` which exists in the bundle but is unreferenced by SKILL.md — the agent may discover it via directory listing; possibly cross-skill refs `../grill-with-docs/CONTEXT-FORMAT.md` (line 68) and `../grill-with-docs/ADR-FORMAT.md` (line 70) if those siblings are present in the install
- **fs-writes**: possibly `CONTEXT.md` or `LANGUAGE.md` updates if the skill documents new domain terms; possibly an ADR file
- **subprocess**: **expected** — SKILL.md line 37 mandates *"use the Agent tool with `subagent_type=Explore` to walk the codebase"*. The Explore subagent invocation should appear in the trace as a Claude Code subagent task
- **network hosts**: none expected (Anthropic API calls happen out-of-container via the Claude Code harness, not from inside the sandbox)

## Caveats / simplifications

- The bundled `*.md` siblings are part of the skill's own context but NOT part of the LLM-prediction input (per our "SKILL.md only" rule). This means the predictor will likely under-predict the bundled-file reads — that's a clean test of the rule.
- "Proposal only" is a deliberate scope-cut to avoid the agent writing the entire refactor (which would balloon the trace)
