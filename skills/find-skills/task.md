# Task — find-skills

## Skill identity

- **Maker / repo**: vercel-labs / skills
- **In-repo path**: `skills/find-skills`
- **Category**: meta (registry-search)
- **Role in sample**: predictable single-host footprint — clean test of "does LLM correctly predict a one-host skill"

## Prompt

```
Use find-skills to discover skills related to "image generation". Return the top 3 by install count, with the `npx skills add` command for the highest.
```

## Rationale

The maker's documented Step 3 is "Run searches if needed (e.g., `npx skills find react performance`)". We mirror that pattern with a different domain. Single-host expected (skills.sh) — the cleanest candidate for testing whether the LLM correctly predicts narrow network footprints.

## Expected observable footprint

- **fs-reads**: `npx` cache, possibly `~/.npm/`
- **fs-writes**: minimal (npm cache updates)
- **subprocess**: `npx`, `node`
- **network hosts**: `skills.sh` (or `vercel.com/skills.sh` redirect), `registry.npmjs.org` for the npx fetch

## Caveats / simplifications

- The npm-registry hit is for `npx skills` package itself, not the skill's stated purpose — interesting "background IO" example for the report
- Pre-installing the `skills` npm package in the container image avoids that npm hit
- SKILL.md Step 2 (line 44) tells the agent to *"check the skills.sh leaderboard"* **before** running the CLI search. Claude Code is likely to satisfy this with a WebFetch to `https://skills.sh/` rather than a subprocess. The trace may therefore show a direct HTTP call to `skills.sh` *before* any `npx` invocation — both ultimately contact the same host, but the request pattern is WebFetch + subprocess, not just subprocess
