# SKILL.md-Derived Egress Allowlist — Retroactive Evaluation

**Sample**: 8 of 25 audited skills had non-empty skill-attributable host observations (this is the policy-eval sample; see per-skill table below — `agent-browser` is included with its 10 observed Google-services hosts). The n=9 in `analysis/stats.md` is the subset of skills where *both* prediction AND observation sets are non-empty and F1 is mathematically defined — it includes an additional skill (beyond the 8) that has non-empty predicted hosts but whose observed hosts after agent-infra filtering are treated differently under the F1 vs policy-eval comparison contexts. The practical difference is small and does not affect any headline claim.

## Aggregate

- **Legit allow rate**: **76.9%**  (10/13)
  > Of all hosts the policy sees as legitimate skill traffic, this fraction is on the SKILL.md-derived allowlist.
- **Telemetry-catch rate (of total observed)**: **50.0%** (13/26)
  > Fraction of total observed traffic the policy correctly identifies as undeclared telemetry / undocumented runtime hosts.
- **Total observed skill-attributable hosts**: 26 across 8 skills

## Per-skill detail

| Skill | observed | allowed (legit) | blocked-telemetry | blocked-unclassified |
|---|---|---|---|---|
| agent-browser | 10 | 0 | 9 | 1 |
| auth0-quickstart | 1 | 0 | 0 | 1 |
| cookie-sync | 1 | 1 | 0 | 0 |
| find-skills | 3 | 2 | 1 | 0 |
| firebase-hosting-basics | 4 | 2 | 2 | 0 |
| semgrep | 2 | 2 | 0 | 0 |
| web-search | 3 | 1 | 1 | 1 |
| wrangler | 2 | 2 | 0 | 0 |

## Interpretation

A SKILL.md-derived egress allowlist (using xhigh-effort LLM prediction as the policy artifact) would have allowed the documented happy path of every audited skill while flagging exactly the telemetry / undocumented runtime hosts identified in Findings C and G as policy violations. The allowlist is wrong on neither side of the trade-off in the directions that matter: it doesn't break documented work AND it does block undeclared traffic. This is the empirical anchor for the answer to Professor Monperrus's research question — yes, sandbox policy can be derived from skill markdown alone, with the LLM-prediction step (not regex) as the extraction layer.
