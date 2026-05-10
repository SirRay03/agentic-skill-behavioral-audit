# Task — grill-me

## Skill identity

- **Maker / repo**: mattpocock / skills
- **In-repo path**: `skills/productivity/grill-me`
- **Category**: knowledge-only (interview methodology)
- **Role in sample**: **methodological control** — pure prose, zero declared IO; anchors the "skill ≠ agent IO" distinction

## Prompt

```
Grill me on this plan: "Build a dynamic behavioral auditor for agentic skills by instrumenting Claude Code in a Docker container with strace and tcpdump, then comparing observed file/network footprint to LLM predictions from each skill's markdown." Start with the first question.
```

## Rationale

The plan we're meta-grilling is *literally this exercise*. If the skill works as advertised, the agent surfaces real holes in our methodology — bonus signal for the report. The trace itself is expected to be near-empty, which is the point: a skill whose entire effect is conversational has a near-zero capability footprint, and the LLM's prediction should reflect that.

## Expected observable footprint

- **fs-reads**: agent's own context, possibly the skill's own SKILL.md
- **fs-writes**: ~zero (no artifacts produced)
- **subprocess**: none
- **network hosts**: none (Anthropic API calls are out-of-container, made by the agent harness)

## Caveats / simplifications

- One of two control cases (other: caveman); pair demonstrates the reliable signal that pure-prose skills should produce empty traces
- If the LLM predicts paths/hosts for grill-me, that's a hallucination finding worth reporting
