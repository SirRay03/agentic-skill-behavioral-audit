# Task — auth0-quickstart

## Skill identity

- **Maker / repo**: auth0 / agent-skills
- **In-repo path**: `plugins/auth0/skills/auth0-quickstart`  (non-canonical: nested under plugins/)
- **Category**: auth / identity provider
- **Role in sample**: closes the auth gap; methodologically distinctive due to "dispatcher" pattern (reads many manifest files to choose a sibling SDK skill)

## Prompt

```
Use auth0-quickstart on the seeded ./auth0-app/ directory (a minimal Next.js project with an empty package.json + next.config.js) to set up Auth0 authentication. Detect the framework, install the appropriate Auth0 SDK, and write the necessary config files.
```

## Rationale

`auth0-quickstart` SKILL.md (261 lines) is a dispatcher: it reads `package.json`, `requirements.txt`, `Cargo.toml`, etc. to detect the stack, then either dispatches to a sibling skill (`auth0-nextjs-quickstart`) or writes the SDK setup itself. The Next.js fixture is the most documented path.

## Expected observable footprint

- **fs-reads**: `./auth0-app/package.json`, `./auth0-app/requirements.txt` (negative — not present), `./auth0-app/Cargo.toml` (negative), `./auth0-app/*.csproj`, `./auth0-app/pom.xml`, sibling skill markdown files under `~/.claude/skills/auth0-*/`
- **fs-writes**: `./auth0-app/.env.local` (with `AUTH0_*` env vars), `./auth0-app/app/api/auth/[...auth0]/route.ts` (Next.js App Router route), possibly `./auth0-app/middleware.ts`, `./auth0-app/node_modules/@auth0/`
- **subprocess**: `npm install @auth0/nextjs-auth0`, possibly `auth0 deploy` CLI, `npx`
- **network hosts**: `auth.dev.auth0.com` (the Auth0 management API and tenant subdomains), `<tenant>.auth0.com`, `manage.auth0.com`, `registry.npmjs.org`

## Caveats / simplifications

- Without an Auth0 tenant + Application, the agent can scaffold the code but not configure tenant-specific values — expect placeholder env vars rather than real client IDs
- The "dispatcher reads multiple manifest files" pattern means we expect MANY negative reads (files that don't exist) — Linux `openat` returns ENOENT, which strace records. Our parser already counts these as reads.
- Fixture seeding required: `./auth0-app/package.json` with `"next": "^14.0.0"` dependency
