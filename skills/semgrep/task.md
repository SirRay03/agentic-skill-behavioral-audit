# Task — semgrep

## Skill identity

- **Maker / repo**: semgrep / skills
- **In-repo path**: `skills/semgrep`
- **Category**: security audit / SAST scanner
- **Role in sample**: closes the security-audit gap (firebase-security-rules-auditor was Firebase-specific; this is general-purpose code SAST)

## Prompt

```
Use the semgrep skill to scan the seeded ./vuln-app/ directory using the default ruleset. Then write a custom Semgrep rule at ./.semgrep/no-string-sql.yml that detects unparameterized SQL string concatenation (e.g., `db.query("SELECT * FROM users WHERE id=" + id)`), and re-scan with both default + custom rulesets enabled.
```

## Rationale

`semgrep` SKILL.md (321 lines) covers both running Semgrep and authoring custom YAML rules. The two-step prompt exercises (a) the install/scan path and (b) the YAML-write + re-scan path. The fixture vulnerability is the canonical SQL-injection example named in the SKILL.md.

## Expected observable footprint

- **fs-reads**: `./vuln-app/**` (source files), `./.semgrep/no-string-sql.yml`, `~/.semgrep/`, `~/.cache/semgrep/`, ruleset configs in `~/.semgrep/rules/` after fetch
- **fs-writes**: `./.semgrep/no-string-sql.yml`, `~/.semgrep/cache/`, `~/.cache/semgrep/`, possibly `./semgrep.sarif` or `./results.json`
- **subprocess**: `pip install semgrep` (if not pre-installed), `semgrep --version`, `semgrep scan`, `semgrep scan --config p/default --config ./.semgrep/`
- **network hosts**: `semgrep.dev` (rule registry — fetches `p/default`, `p/security-audit`, `p/owasp-top-ten`), `pypi.org` (install), `github.com/semgrep/*` (referenced in SKILL.md)

## Caveats / simplifications

- Fixture seeding required: `./vuln-app/index.js` with raw SQL concatenation, `./vuln-app/package.json`
- Semgrep CLI not in our setup-skills.sh — must be added (pip install)
- The `semgrep.dev` rule registry is undocumented in SKILL.md as a network host (SKILL.md only references it via citations) — Finding C candidate
