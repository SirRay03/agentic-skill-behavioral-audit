# Task — agent-browser

## Skill identity

- **Maker / repo**: vercel-labs / agent-browser
- **In-repo path**: `skills/agent-browser`
- **Category**: browser-broad (Rust CLI, Chrome via CDP)
- **Role in sample**: broadest declared surface — main treatment for "files / web / test" verb cluster

## Prompt

```
Open https://news.ycombinator.com with agent-browser. Take a screenshot of the front page and save it to ./hn.png. Then extract and return the top 5 story titles.
```

## Rationale

Exercises three of the maker's documented verbs (navigate, screenshot, extract) in a single minimal task. HN front page is stable enough for reproducibility. This is the most likely candidate to produce a large declared-vs-observed gap, which is exactly what we want for the report's headline finding.

## Expected observable footprint

- **fs-reads**: agent-browser binary, browser profile dir, Chromium/Chrome binary, agent-browser's bundled skill content (fetched via `skills get core`)
- **fs-writes**: `./hn.png`, browser profile cache, possibly downloads dir
- **subprocess**: `agent-browser` (called at least twice — once for `skills get core` discovery, once for the actual browse), Chromium/Chrome
- **network hosts**: `news.ycombinator.com`, plus likely a CDN, plus possibly agent-browser self-update or telemetry endpoints

## Caveats / simplifications

- The skill's install command is `npm i -g agent-browser && agent-browser install` — pre-install in container image to avoid contaminating trace with self-install IO
- SKILL.md mandates `agent-browser skills get core` as a discovery step before any other command (lines 21, 33-39 of SKILL.md). Expect this subprocess and a possible network call to fetch the workflow content even before the navigate/screenshot/extract commands begin
- Chromium binary in the container will have its own large fs surface; we'll need to filter generic browser ops vs skill-attributable ops in analysis
- This skill exemplifies the **live-loading pattern** documented in methodology.md §11 — SKILL.md is essentially a discovery stub, with the actual workflow content fetched at runtime via `agent-browser skills get core`. The LLM predictor reading the stub alone cannot fully predict the runtime behaviour. Featured as a discussion-section finding in the final report (see decision-log "Cross-cutting Finding B").
