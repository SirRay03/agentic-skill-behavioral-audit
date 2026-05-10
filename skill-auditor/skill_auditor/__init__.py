"""skill-auditor — behavioural audit toolkit for agentic skills.

Three subcommands wrap the audit pipeline from the parent kth-skill-audit-exercise:

  skill-auditor predict <SKILL.md>   — emit prediction.json (LLM-extracted IO surface)
  skill-auditor audit <SKILL.md> [--task <prompt>]
                                     — full P3 (predict) + P4 (instrumented run)
  skill-auditor policy <SKILL.md>    — emit skill-policy.json (capability bundle)

The package is intentionally thin — it wraps the existing harness scripts
(predict.py, run-skill.sh, policy-bundle-generator.py) so that operators can
install the toolkit via `pip install skill-auditor` without cloning the repo.
"""

__version__ = "0.1.0"
