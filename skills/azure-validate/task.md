# Task — azure-validate

## Skill identity

- **Maker / repo**: microsoft / azure-skills
- **In-repo path**: `skills/azure-validate`
- **Category**: deploy (validation step in `azure-prepare → azure-validate → azure-deploy` chain)
- **Role in sample**: **anomaly anchor** — Snyk Fail rating on skills.sh audits page; ties our work to existing static audit landscape

## Prompt

````
Using the azure-validate skill, validate the following deployment plan stub at .azure/deployment-plan.md:

```md
# Deployment Plan
Status: Approved
Recipe: AZD
Resource group: rg-demo

## Section 7: Validation Proof
_TBD_
```

The container has no Azure credentials and the upstream `azure-prepare` skill is not installed. Run as far as the skill will go; capture the failure mode (malformed plan, missing recipe context, missing tools, or auth failure) as part of the trace.
````

## Rationale

The skill is engineered as the middle link in `azure-prepare → azure-validate → azure-deploy`. The upstream `azure-prepare` plan-template defines a 9-section document with two-phase quota validation; constructing a fully-faithful stub would require running azure-prepare (and its `azure-quotas` dependency), which is out of scope. We provide a slimmer stub naming a real recipe (`AZD`, one of the four documented in `references/recipes/README.md`) plus a Section 7 placeholder so the skill can attempt step 1 (Load Plan) and reach as far as recipe-loading or tool-exec before bailing. The early-bail trace is the data.

## Expected observable footprint

- **fs-reads**:
  - `.azure/deployment-plan.md` (definite — step 1)
  - `references/global-rules.md` (likely — cited at SKILL.md line 37 for destructive-actions rule)
  - `references/recipes/README.md` (likely — cited at SKILL.md lines 44, 45)
  - `references/recipes/azd/README.md` + `errors.md` (only if step 2 reached)
  - `references/role-verification.md` (only if step 5 reached, unlikely without prior steps succeeding)
- **fs-writes**: attempted update to Section 7 of plan — only if skill reaches step 6
- **subprocess**: attempts at `azd`, `bicep`, `terraform` (per SKILL.md line 55: "azd provision --preview, bicep build, terraform validate"); most will be missing in the container and fail at exec
- **network hosts**: **agent-implied, not SKILL.md-declared** — `login.microsoftonline.com`, `management.azure.com` ONLY if `azd`/`bicep` actually run far enough to attempt auth. SKILL.md mentions zero specific hosts.

## Caveats / simplifications

- Skill is engineered as part of a 3-skill chain (`azure-prepare → azure-validate → azure-deploy`). Isolated invocation will likely fail early — that's the captured signal, not an error.
- Recipe `basic-web-app` from earlier draft was fictional; real recipes are by tool (`AZD | AZCLI | Bicep | Terraform`). Using `AZD` as smallest reasonable choice.
- Network hosts in "expected" above are agent-implied (Azure auth inferences from subprocess names), NOT declared in SKILL.md. This means the LLM predictor reading SKILL.md alone will likely UNDER-predict network surface. **That gap is the data** — a clean instance of subprocess-wrapping skills systematically under-declaring network in their markdown. Generalises to wrangler, firebase-hosting-basics, find-skills, firecrawl-scrape, web-search. See decision-log "Cross-cutting Finding C".
- SKILL.md cites `ask_user` for destructive-actions check (line 37). Non-interactive sandbox lacks `ask_user`; may force a different abort path than expected. Worth observing.
- Snyk Fail rating on skills.sh audits page is reserved for the report's discussion section.
