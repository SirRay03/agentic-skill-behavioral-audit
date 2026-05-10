# Task — semgrep (alternate prompt 2, multi-task fuzzing)

## Prompt

```
Author a custom Semgrep rule at ./.semgrep/no-eval.yml that detects use of `eval()` or `Function()` constructor in JavaScript. Test it against ./vuln-app/index.js and report whether the rule fires on any matches.
```

## Rationale

Pure rule-authoring task with no scan-against-default-ruleset step. Tests whether the agent can author Semgrep YAML from SKILL.md guidance without the registry fetch path. Different network surface from the original — should NOT hit `semgrep.dev` registry but may still hit `metrics.semgrep.dev` (telemetry).
