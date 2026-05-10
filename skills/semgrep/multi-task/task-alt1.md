# Task — semgrep (alternate prompt 1, multi-task fuzzing)

## Prompt

```
Run `semgrep scan --config p/owasp-top-ten ./vuln-app/` to scan the seeded vulnerable JS app against the OWASP Top Ten ruleset. Report the highest-severity finding.
```

## Rationale

Different ruleset (`p/owasp-top-ten` vs the original's default ruleset + custom rule). Tests rule-registry fetch from a different bundle (semgrep.dev redirect to specific OWASP ruleset URL). Should still hit `metrics.semgrep.dev` (Finding G — telemetry beacon fires regardless of ruleset).
