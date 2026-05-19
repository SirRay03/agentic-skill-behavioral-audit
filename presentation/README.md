# Presentation — KTH ASSERT lightning talk (2026-05-18)

The deck delivered to Professor Martin Monperrus and ASSERT PhD students on **2026-05-18** as the synthesis of this audit. The talk is a 12-minute lightning summary of the work in [`../report.md`](../report.md), structured around four methodological acts (measure → stress-test → close-the-gap → probe-the-adversary) and a live dashboard tour.

## View the deck

- **Live**: [sirray03.github.io/agentic-skill-behavioral-audit/talk/](https://sirray03.github.io/agentic-skill-behavioral-audit/talk/)
- **Local**: open [`slides.html`](slides.html) in any modern browser. Self-contained Reveal.js 5.x — no build step, no `node_modules`. Figures bundled under [`figures/`](figures/).

## Folder contents

| Path | Purpose |
|---|---|
| [`slides.html`](slides.html) | Reveal.js deck — 11 main slides + 6 backup slides + embedded styles |
| [`figures/`](figures/) | The six audit figures referenced by the deck (`fig-01..06.svg/.png`), plus per-slide screenshots (`slide-s01..s10.png`, `slide-backup-01..06.png`) captured at 1280×800 |
| [`scripts/`](scripts/) | Two utilities — `take-dashboard-screenshots.mjs` (Playwright capture of `/findings`, `/skills/wrangler`, `/mutation-suite`, `/policy` for offline fallback) and `check-slides-layout.mjs` (overflow auditor that flags any slide whose body exceeds the 800px canvas) |

## Deck structure

| # | Title | Beat |
|---|---|---|
| S1 | Title — depth vs breadth | Framing and one-sentence thesis |
| S2 | Why depth on n=25, not breadth | Liu et al. + Socket as the scale-context this work complements |
| S3 | Pipeline P0 → P5 | The six-step instrumentation spine |
| S3.5 | **Four acts — how the work evolved** | The narrative arc across the six enrichments |
| S4 | Hosts F1 = 0.431 — bimodal | Headline empirical claim |
| S5 | Under-declaration is vendor telemetry | The mechanism behind the bimodal split |
| S6 | Defense-in-depth — 6 of 6 contained | The mutation suite + L1 brittleness ablation |
| S7 | Predictor identity is load-bearing | Finding N — cross-LLM Jaccard 0.41 |
| S8 | SKILL.md → policy 77% / 50% | The constructive answer with three asterisks |
| S9 | Limits + what two more weeks would buy | Blind spots and seven honest corrections |
| S10 | Live demo + closing map | Dashboard tour → five-layer stack mapped onto the three subgoals |
| B1–B6 | Backup slides | Forest plot · failure-mode taxonomy · mutation matrix · McNemar+Wilcoxon · augmentation lift · Finding H decomposition |

## Reproducing the deck locally

```bash
# Browse the deck
open presentation/slides.html        # macOS
xdg-open presentation/slides.html    # Linux
start presentation/slides.html       # Windows

# Re-capture dashboard screenshots (requires Playwright)
cd presentation/scripts
node take-dashboard-screenshots.mjs

# Verify no slide overflows the 1280×800 canvas
node check-slides-layout.mjs
```

## Companion artefacts

| Artefact | Where |
|---|---|
| Full report (14 pages, PDF) | [`../report.pdf`](../report.pdf) |
| Full report (markdown source) | [`../report.md`](../report.md) |
| Executive summary (1 page) | [`../EXECUTIVE_SUMMARY.md`](../EXECUTIVE_SUMMARY.md) |
| Skill-author guidance (6-practice checklist) | [`../SKILL_AUTHORING_GUIDE.md`](../SKILL_AUTHORING_GUIDE.md) |
| Methodology spine | [`../methodology.md`](../methodology.md) |
| Decision log | [`../DECISIONS.md`](../DECISIONS.md) |
| Interactive dashboard | [sirray03.github.io/agentic-skill-behavioral-audit/](https://sirray03.github.io/agentic-skill-behavioral-audit/) |

## License

The deck content, figures, and scripts in this folder are MIT-licensed alongside the rest of the repository (see [`../LICENSE`](../LICENSE)). The deck cites Liu et al. (2026) and Socket; both retain their original attributions.
