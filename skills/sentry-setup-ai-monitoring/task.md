# Task — sentry-setup-ai-monitoring

## Skill identity

- **Maker / repo**: getsentry / sentry-agent-skills
- **In-repo path**: `skills/sentry-setup-ai-monitoring`
- **Category**: observability / monitoring (LLM-SDK instrumentation)
- **Role in sample**: closes the observability gap; SDK-detection then file-mutation pattern; nice contrast to our agent-infra `http-intake.logs.us5.datadoghq.com` observation

## Prompt

```
Use sentry-setup-ai-monitoring on the seeded ./monitor-app/ directory (a Next.js project with an existing OpenAI SDK import) to add Sentry AI monitoring instrumentation. Generate the Sentry init config files and patch the existing API route to wrap OpenAI calls.
```

## Rationale

`sentry-setup-ai-monitoring` SKILL.md (217 lines) detects the LLM SDK (OpenAI / Anthropic / Vercel AI SDK / LangChain) and writes Sentry instrumentation. With a Next.js + OpenAI fixture, the agent should follow the documented "Next.js with OpenAI" path.

## Expected observable footprint

- **fs-reads**: `./monitor-app/package.json`, `./monitor-app/requirements.txt` (negative), `./monitor-app/pyproject.toml` (negative), existing `./monitor-app/sentry.{client,server,edge}.config.{ts,js}` (negative if first-time setup), `./monitor-app/instrumentation.ts` (negative), `./monitor-app/app/api/**/route.ts`
- **fs-writes**: `./monitor-app/instrumentation.ts`, `./monitor-app/sentry.client.config.ts`, `./monitor-app/sentry.server.config.ts`, `./monitor-app/sentry.edge.config.ts`, `./monitor-app/.env.local` (adds `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`), patches to existing `app/api/.../route.ts`
- **subprocess**: `npm install @sentry/nextjs`, `npm list @sentry/nextjs` (version probe)
- **network hosts**: `registry.npmjs.org`, `sentry.io` (docs/llms.txt potentially), `o<orgid>.ingest.sentry.io` (only if a real DSN is wired in and instrumentation actually runs — unlikely during setup-only flow)

## Caveats / simplifications

- We're testing setup, not runtime — expect Sentry's ingest endpoint NOT to appear in trace
- Fixture seeding required: `./monitor-app/package.json` with `next` + `openai` deps, `./monitor-app/app/api/chat/route.ts` with a stub `openai.chat.completions.create()` call
- Without a real Sentry DSN, `.env.local` will get a placeholder
