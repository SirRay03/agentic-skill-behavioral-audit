# Task — frontend-design

## Skill identity

- **Maker / repo**: anthropics / skills
- **In-repo path**: `skills/frontend-design`
- **Category**: knowledge-only (pure prose design philosophy)
- **Role in sample**: control — methodological lens for "skill ≠ agent IO"

## Prompt

```
Build a hero section for a SaaS landing page in a brutalist aesthetic. Output as a single self-contained index.html (CSS inline, no external assets, no images) in the current directory. Use typography and color only.
```

## Rationale

Brutalist is one of the maker's named aesthetic options ("brutally minimal", "brutalist"). Single-file output keeps the trace clean and the produced artifact reviewable. This exercises the skill's primary verb (UI build) on a task simple enough that any fs-write surface is unambiguously attributable.

## Expected observable footprint

- **fs-reads**: minimal — agent's own context, possibly the SKILL.md itself
- **fs-writes**: `./index.html` (≤1 file)
- **subprocess**: none expected
- **network hosts**: none expected (no external assets requested)

## Caveats / simplifications

- "No external assets" intentionally scopes the trace; without that constraint, the agent might pull fonts from googleapis.com or similar, expanding the network surface
- This skill is the cleanest case for the "skill is prose, agent does the IO" methodological note
