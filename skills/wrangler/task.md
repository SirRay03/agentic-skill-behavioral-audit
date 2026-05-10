# Task — wrangler

## Skill identity

- **Maker / repo**: cloudflare / skills
- **In-repo path**: `skills/wrangler`
- **Category**: deploy (Cloudflare Workers CLI)
- **Role in sample**: third deploy maker (Cloudflare) for stratification; CLI subprocess footprint

## Prompt

```
Set up a minimal Cloudflare Worker in ./worker/ by writing a wrangler.jsonc and src/index.ts based on the SKILL.md "Minimal Config" example, then run `npx wrangler deploy --dry-run` to validate the bundle without actually deploying.
```

## Rationale

The two documented init paths (`npx wrangler init`, `npx create-cloudflare@latest`) both delegate to the interactive `create-cloudflare` wizard, which hangs in non-interactive sandbox mode regardless of flags. Hand-writing a minimal config from the SKILL.md "Minimal Config" snippet (lines 72-81) sidesteps the interactivity trap and still exercises the documented `--dry-run` validation path, which appears in the Quick Reference (line 61), the Deployment section (line 232), and the Best Practices list (line 921).

## Expected observable footprint

- **fs-reads**: npm caches (for `npx wrangler` package fetch), `./worker/wrangler.jsonc`, `./worker/src/index.ts`, possibly `./node_modules/wrangler/config-schema.json` (referenced by `$schema` field and explicitly named as a retrieval source on SKILL.md line 17)
- **fs-writes**: `./worker/wrangler.jsonc`, `./worker/src/index.ts`, `./worker/.wrangler/state/` (per SKILL.md line 894 — local state dir), possibly `./worker/node_modules/`
- **subprocess**: `wrangler --version` install probe (per SKILL.md lines 22-26), `npx`, `wrangler`, `node`, possibly `npm install -D wrangler@latest` if probe fails (per SKILL.md line 31), possibly `esbuild` (bundler)
- **network hosts**: `developers.cloudflare.com` (SKILL.md lines 16, 18 mandate retrieval from this host — *"Prefer retrieval over pre-training"*); `registry.npmjs.org` for package fetches; `api.cloudflare.com` for auth probe (will fail without creds, but the connect attempt should be visible in the trace)

## Caveats / simplifications

- `--dry-run` plus stub auth keeps actual deployment from happening
- Hand-writing config skips the interactive `create-cloudflare` wizard that modern `wrangler init` delegates to (verified: SKILL.md does not document a non-interactive flag combination)
- Watch for `node_modules` install if wrangler isn't pre-cached — could explode trace volume; mitigation is pre-installing wrangler in container image
- If `--dry-run` aborts before the auth probe (e.g., bundle-only validation), `api.cloudflare.com` may not appear — that's a meaningful prediction-vs-observation data point
- The `developers.cloudflare.com` retrieval calls are SKILL.md-mandated — under-predicting this host would be a noteworthy LLM-prediction miss to call out in the report
