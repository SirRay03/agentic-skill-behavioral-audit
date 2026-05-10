# Task — caveman

## Skill identity

- **Maker / repo**: juliusbrussee / caveman
- **In-repo path**: `caveman` (lives at repo root, not under `skills/` — outlier)
- **Category**: knowledge-only (terse output mode)
- **Role in sample**: **methodological control #2** — pure prose, zero declared IO; pairs with grill-me

## Prompt

```
Activate caveman mode at intensity level "full". Then explain in one paragraph: how does HTTPS work?
```

## Rationale

Tests the skill's verb (compress communication) on a topic where compression is testable (HTTPS has well-known concept density). The trace is expected to be near-empty, which is the point: this skill's entire effect is on the agent's output style, not on the environment.

## Expected observable footprint

- **fs-reads**: agent context, possibly the skill's own SKILL.md
- **fs-writes**: ~zero
- **subprocess**: none
- **network hosts**: none

## Caveats / simplifications

- Second of two control cases (paired with grill-me) — together they anchor the methodological point that pure-prose skills should have empty traces, and any predicted IO would be hallucination
