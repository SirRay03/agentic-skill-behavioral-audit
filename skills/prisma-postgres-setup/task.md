# Task — prisma-postgres-setup

## Skill identity

- **Maker / repo**: prisma / skills
- **In-repo path**: `prisma-postgres-setup`  (note: NOT under `skills/` — repo-root-level path)
- **Category**: database schema / migration
- **Role in sample**: closes the DB gap; CLI provisioning + multi-host auth flow + heavy npm install footprint

## Prompt

```
Use prisma-postgres-setup to scaffold a new Node.js project in ./prisma-app/ that uses Prisma with a Prisma Postgres database. Define a minimal `User` model (id, email, name) in the schema, then generate the Prisma client.
```

## Rationale

`prisma-postgres-setup` SKILL.md (263 lines) provisions a Prisma Postgres project, writes `.env`, generates schema, runs migrations. The minimal `User` model is the canonical SKILL.md example. We stop at `generate` (not `migrate dev`) to avoid actually creating cloud DB resources without the user's explicit consent — but this still exercises the npm-install + Prisma CLI invocation + Management API auth probe.

## Expected observable footprint

- **fs-reads**: SKILL.md, `./prisma-app/package.json`, `./prisma-app/prisma/schema.prisma`, `./prisma-app/.env`, `~/.npm/_cacache/`, `node_modules/@prisma/`
- **fs-writes**: `./prisma-app/.env` (with DATABASE_URL placeholder), `./prisma-app/prisma/schema.prisma`, `./prisma-app/node_modules/.prisma/client/` (generated client), possibly `./prisma-app/prisma/migrations/<ts>_init/migration.sql` if `migrate dev` is invoked
- **subprocess**: `npm init -y`, `npm install -D prisma`, `npm install @prisma/client`, `npx prisma init`, `npx prisma generate`, possibly `npx prisma migrate dev`
- **network hosts**: `api.prisma.io` (Management API for project provisioning), `accounts.prisma.io` (auth), `pris.ly` (short-link redirector to docs), `registry.npmjs.org`, `binaries.prisma.sh` (engine binaries)

## Caveats / simplifications

- Without a Prisma Cloud account / API key, the provisioning step will fail at `accounts.prisma.io` auth — agent should fall back to scaffolding only, which still exercises the npm + schema-write paths
- Prisma engine binary download from `binaries.prisma.sh` is undocumented in SKILL.md — strong Finding C candidate
