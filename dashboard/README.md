# Agentic Skill Auditor — Dashboard

Companion interactive site for *A Dynamic Behavioural Auditor for Agentic Skills*
(Rayhan Putra, 2026-05-11). Sister project to the audit itself; **does not modify
any audit content**. Reads `../skills/`, `../analysis/`, `../report.md`, and
`../DECISIONS.md` at build time to populate content collections.

**Live**: https://sirray03.github.io/agentic-skill-behavioral-audit/

## Stack

- **Astro 5** — static-site generator, content collections, MDX
- **Tailwind 4** — via `@tailwindcss/vite`
- **Python 3** — pre-build data extraction (`scripts/build-data.py`)
- **GitHub Pages** — deploy target (free, public repo)

## Local development

All commands assume the working directory is `dashboard/`.

```bash
# Install deps (first time only)
npm install

# Dev server
npm run dev

# Production build
npm run build

# Regenerate data (only when audit data changes)
npm run data
```

The `src/data/generated/*.json` files and `public/figures/*` are pre-baked and
committed so the deploy server doesn't need Python. Run `npm run data` to
regenerate them after editing anything under `../skills/`, `../analysis/`,
`../report.md`, etc.

## Deploy (GitHub Pages)

Configured via `.github/workflows/deploy.yml` at repo root. On every push to
`main` that touches `dashboard/**`, the workflow:

1. Installs deps via `npm ci`
2. Runs `npm run build` with `BASE=/agentic-skill-behavioral-audit` and
   `SITE=https://sirray03.github.io` injected as env vars (so all internal
   links pick up the project-pages base path)
3. Uploads `dashboard/dist/` as a Pages artefact
4. `actions/deploy-pages@v4` publishes it

Live URL: https://sirray03.github.io/agentic-skill-behavioral-audit/

For local builds at the same base path:

```bash
BASE=/agentic-skill-behavioral-audit SITE=https://sirray03.github.io npm run build
```

For local preview at `/`, just run `npm run dev` — no env vars needed.

## File map

```
dashboard/
├── README.md                     ← you are here
├── package.json
├── astro.config.mjs
├── tsconfig.json
├── scripts/
│   └── build-data.py             ← reads ../skills, ../analysis, emits src/data/generated/
├── src/
│   ├── layouts/
│   │   └── Layout.astro          ← shared header + nav + footer
│   ├── pages/                    ← one file per route
│   │   ├── index.astro           ← landing
│   │   ├── findings/             ← /findings + /findings/[slug]
│   │   ├── skills/               ← /skills + /skills/[id]
│   │   ├── mutation-suite.astro
│   │   ├── policy.astro
│   │   ├── methodology.astro
│   │   ├── figures.astro
│   │   └── about.astro
│   ├── components/               ← StatCard, FindingCard, SkillRow, etc.
│   ├── data/
│   │   └── generated/            ← committed; regenerate via `npm run data`
│   ├── lib/
│   │   ├── markdown.ts           ← marked wrapper for finding-body rendering
│   │   └── url.ts                ← base-path helper (u(path)) for deploy compat
│   └── styles/
│       └── global.css            ← design tokens + prose styles
```

## What the data extraction script does

`scripts/build-data.py` reads:

- `../skills/<id>/{prediction,prediction-fresh,prediction-codex,trace,skill-policy}.json`
  — for n=25 production skills + 6 mutations + 1 adversarial + 3 augmented
- `../analysis/per-skill.json` — canonical F1 table
- `../analysis/summary.json` — aggregate F1
- `../analysis/{stats,policy-eval,policy-enforcement,mutation-suite,...}.json`
  — analysis outputs
- `../report.md` — narrative
- `../EXECUTIVE_SUMMARY.md` — TL;DR

…and emits to `src/data/generated/`:

- `skills.json` — flat array of skill records (id, category, role, F1 axes, has_codex, has_realcreds, has_policy, prediction_summary, observed_summary)
- `findings.json` — 15-finding catalogue keyed by letter A-O
- `analysis.json` — analysis-doc index (slug → title, category, summary, body_md)
- `aggregates.json` — headline numbers
- `mutation-suite.json` — 6×4 table
- `policy.json` — 5 policy bundles
- `figures.json` — 6 figures + captions

## Non-goals

- No modification of `../report.md`, `../EXECUTIVE_SUMMARY.md`, or any audit content
- No re-running of experiments or re-generation of figures
- No commits to the underlying repo from the dashboard build
