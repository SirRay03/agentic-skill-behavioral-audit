# Task — wrangler (alternate prompt 1, multi-task fuzzing)

## Prompt

```
Generate TypeScript types for an existing Cloudflare Worker by running `npx wrangler types` against the wrangler.jsonc at ./worker/wrangler.jsonc. Verify the generated `worker-configuration.d.ts` file lists the worker's bindings (variables, KV namespaces if any).
```

## Rationale

Different documented verb than the original (which was `--dry-run` of `deploy`). `wrangler types` is documented in SKILL.md (line 894-ish, Best Practices) and exercises a different code path (no auth probe, no deploy bundle, but does write a `.d.ts` file).
