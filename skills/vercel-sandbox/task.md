# Task — vercel-sandbox

## Skill identity

- **Maker / repo**: vercel-labs / agent-browser
- **In-repo path**: `skill-data/vercel-sandbox`  (non-canonical: NOT under `skills/`, lives under `skill-data/` — tests our path-resolution robustness)
- **Category**: deploy / Vercel-specific (microVM agent runtime via Vercel Sandbox)
- **Role in sample**: closes the Vercel gap; non-canonical bundling path is itself methodologically interesting; family-tied to the agent-browser skill we already audited

## Prompt

```
Use vercel-sandbox to add an agent-browser-powered API route to the seeded ./next-app/ Next.js project. The route should accept a URL query param, scrape the page title via agent-browser running inside a Vercel Sandbox microVM, and return the title as JSON.
```

## Rationale

`vercel-sandbox` SKILL.md (280 lines) wraps `@vercel/sandbox` + `agent-browser` together. The "scrape page title from URL" task is the canonical SKILL.md example — exercises the API-route write, npm install, and Vercel Sandbox provisioning paths.

## Expected observable footprint

- **fs-reads**: `./next-app/package.json`, `./next-app/next.config.{js,ts}`, `./next-app/app/api/**` for existing routes
- **fs-writes**: `./next-app/app/api/scrape/route.ts` (the new API route), `./next-app/.env.local` (with `VERCEL_TOKEN`, `VERCEL_TEAM_ID`, possibly `AGENT_BROWSER_API_KEY`), `./next-app/node_modules/agent-browser/`, `./next-app/node_modules/@vercel/sandbox/`
- **subprocess**: `npm install agent-browser @vercel/sandbox`, possibly `vercel deploy` or `vercel dev`, `npx`
- **network hosts**: `api.vercel.com` (Sandbox provisioning), `*.vercel.app` (the deployed function URL), `vercel.com` (auth/dashboard), `registry.npmjs.org`, possibly `agent-browser` skill's own hosts inherited via the wrapped invocation

## Caveats / simplifications

- Without a Vercel team token, the agent can scaffold the route but not actually provision a sandbox — expect placeholder env vars and the agent stopping before `vercel deploy`
- Fixture seeding required: `./next-app/package.json` (Next.js 14+), `./next-app/app/page.tsx` placeholder, `./next-app/next.config.js`
- Methodologically interesting nesting: a Vercel Sandbox running an `agent-browser` instance — TWO layers of opaque routing (Vercel Sandbox API + agent-browser's Browserbase integration) on top of the Anthropic harness layer. Maximally adversarial conditions for our tracing approach.
