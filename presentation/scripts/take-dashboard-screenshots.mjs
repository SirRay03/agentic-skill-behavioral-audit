// Capture dashboard fallback screenshots for the KTH ASSERT lightning talk.
// Run from repo root:
//
//   cd presentation/scripts
//   node take-dashboard-screenshots.mjs
//
// First-time setup (Windows PowerShell):
//
//   npm install -g playwright
//   playwright install chromium
//
// Outputs PNGs into presentation/figures/dashboard-NN.png at 1440×900,
// deviceScaleFactor 2 (Retina-equivalent), full-page false (above-the-fold).

import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { mkdirSync } from 'fs';

const BASE = 'https://sirray03.github.io/agentic-skill-behavioral-audit';
const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(__dirname, '..', 'figures');

mkdirSync(OUT_DIR, { recursive: true });

// Six stops in the demo click-path. If a slug is wrong, the script logs the
// failure and continues — fix the URL and re-run only the failing entry.
const SHOTS = [
  {
    name: 'dashboard-01-landing.png',
    path: '/',
    waitFor: 'h1',
    fullPage: false,
    note: 'hero + headline stats',
  },
  {
    name: 'dashboard-02-finding-c.png',
    path: '/findings/cli-wrapping-network-underdeclaration/',
    waitFor: 'h1',
    fullPage: true,
    note: 'Finding C deep-dive',
  },
  {
    name: 'dashboard-03-skill-wrangler.png',
    path: '/skills/wrangler/',
    waitFor: 'h1',
    fullPage: true,
    note: 'per-skill drill-down with prediction + trace blocks',
  },
  {
    name: 'dashboard-04-mutation-suite.png',
    path: '/mutation-suite/',
    waitFor: 'h1',
    fullPage: true,
    note: '6x4 mutation × defense-layer heatmap',
  },
  {
    name: 'dashboard-05-policy.png',
    path: '/policy/',
    waitFor: 'h1',
    fullPage: true,
    note: '77/50 + three asterisks',
  },
  {
    name: 'dashboard-06-findings-catalog.png',
    path: '/findings/',
    waitFor: 'h1',
    fullPage: false,
    note: '15 findings grouped by pattern (above-the-fold only)',
  },
];

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });

  let okCount = 0;
  for (const shot of SHOTS) {
    const url = BASE.replace(/\/$/, '') + shot.path;
    const page = await ctx.newPage();
    try {
      console.log(`→ ${shot.name}  ${url}`);
      const resp = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      if (!resp || resp.status() >= 400) {
        throw new Error(`HTTP ${resp ? resp.status() : 'no response'}`);
      }
      // Best-effort wait for headline content
      try {
        await page.waitForSelector(shot.waitFor, { timeout: 5000 });
      } catch {
        // not fatal — proceed with screenshot anyway
      }
      // Tiny settle for fonts/figures
      await page.waitForTimeout(400);
      await page.screenshot({
        path: join(OUT_DIR, shot.name),
        fullPage: shot.fullPage,
      });
      console.log(`  ok — ${shot.note}`);
      okCount += 1;
    } catch (err) {
      console.error(`  FAIL — ${err.message}`);
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log(`\n${okCount} / ${SHOTS.length} screenshots captured`);
  console.log(`Saved to: ${OUT_DIR}`);
  if (okCount < SHOTS.length) process.exit(1);
})();
