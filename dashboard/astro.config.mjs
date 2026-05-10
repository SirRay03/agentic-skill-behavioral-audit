// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';

// `BASE` and `SITE` are injected at deploy time (e.g. by the GH Pages action).
// Locally they're undefined, so the site builds with base="/" and works at
// http://localhost:4321/. On deploy:
//   BASE=/agentic-skill-behavioral-audit
//   SITE=https://sirray03.github.io
const base = process.env.BASE || '/';
const site = process.env.SITE || undefined;

export default defineConfig({
  site,
  base,
  integrations: [mdx()],
  vite: {
    plugins: [tailwindcss()],
  },
  trailingSlash: 'never',
  build: {
    format: 'directory',
  },
});
