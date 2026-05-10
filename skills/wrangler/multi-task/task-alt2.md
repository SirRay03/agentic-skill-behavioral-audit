# Task — wrangler (alternate prompt 2, multi-task fuzzing)

## Prompt

```
List all current Cloudflare KV namespaces using `npx wrangler kv namespace list`. Report the result; if the auth probe fails, report the failure mode without retrying.
```

## Rationale

Tests the auth-probe path (`api.cloudflare.com`) that `--dry-run` skips. Documented in SKILL.md but exercises a different observable surface (auth-token check + KV-namespace API call). Real-creds variant unlocks this; stub-creds will fail at the auth boundary.
