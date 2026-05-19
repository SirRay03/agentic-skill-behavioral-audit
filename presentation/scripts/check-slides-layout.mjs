// Render every slide in slides.html via Reveal's URL hash and screenshot it.
// Used for layout debugging — outputs presentation/figures/slide-NN.png
//
// Run from any cwd:
//   $env:NODE_PATH = "C:\Users\RaySi\AppData\Roaming\npm\node_modules\@playwright\cli\node_modules"
//   node presentation/scripts/check-slides-layout.mjs

import { pathToFileURL as _ptfu } from 'url';
const PW_PATH = 'C:\\Users\\RaySi\\AppData\\Roaming\\npm\\node_modules\\@playwright\\cli\\node_modules\\playwright\\index.mjs';
const { chromium } = await import(_ptfu(PW_PATH).href);
import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, join, resolve } from 'path';
import { mkdirSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SLIDES_PATH = resolve(__dirname, '..', 'slides.html');
const OUT_DIR = resolve(__dirname, '..', 'figures');
mkdirSync(OUT_DIR, { recursive: true });

const SLIDES_URL = pathToFileURL(SLIDES_PATH).href;

// Main deck has 10 slides (S1..S10), backup has 6 sections (B1..B6).
// Reveal counts all top-level sections sequentially in hash mode (#/n).
const SLIDE_COUNT = 16;

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const ctx = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  });
  const page = await ctx.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error') console.error(`[console.error]`, msg.text());
  });

  console.log(`→ ${SLIDES_URL}`);
  await page.goto(SLIDES_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForSelector('.reveal .slides', { timeout: 10000 });
  await page.waitForTimeout(500);

  for (let i = 0; i < SLIDE_COUNT; i++) {
    const label = i < 10 ? `s${(i + 1).toString().padStart(2, '0')}` : `backup-${(i - 9).toString().padStart(2, '0')}`;
    const out = join(OUT_DIR, `slide-${label}.png`);
    await page.goto(`${SLIDES_URL}#/${i}`, { waitUntil: 'load' });
    await page.waitForTimeout(450); // settle transitions + fonts
    // Reveal a fragment on S10 (slide index 9) to capture the layered stack
    if (i === 9) {
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(300);
    }
    await page.screenshot({ path: out, fullPage: false });
    console.log(`  ${label}.png — saved`);
  }

  await browser.close();
  console.log(`\nSaved ${SLIDE_COUNT} screenshots to ${OUT_DIR}`);
})();
