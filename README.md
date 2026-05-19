# A Dynamic Behavioural Auditor for Agentic Skills

Empirical audit of the declared-vs-observed behavioural footprint of 25 production-grade *agentic skills* (markdown contracts that ship with prompt instructions for AI coding agents like Claude Code or OpenAI Codex CLI). Combines instrumented runtime tracing (`strace` + `tcpdump`) with LLM-only prediction from each skill's SKILL.md text, then quantifies the gap with bootstrap-confidence-interval F1, McNemar's, Wilcoxon, and Mann-Whitney statistics.

This is the entry-point exercise for Professor Monperrus's open thesis topic *"Automatic Hardening of Agentic Skills"* (KTH ASSERT) and operates in the same threat surface as [Liu et al. (2026) *"Agent Skills in the Wild"*](https://arxiv.org/abs/2601.10338) (n=42,447 skills, 26.1% vulnerable) and [Socket's deployed skills.sh scanner](https://socket.dev/blog/socket-brings-supply-chain-security-to-skills) (60,000+ skills, 94.5% precision / 98.7% recall) — but goes deep on a small sample where they go broad.

---

## At a glance

| | |
|---|---|
| **Sample** | 25 production skills + 1 synthetic adversarial demo + 6 attack-pattern mutations + 3 augmented-SKILL.md variants |
| **Headline empirical claim** | CLI-wrapping skills systematically under-declare their network surface — mean hosts F1 = **0.431** across 25 production skills (n=6 with defined F1); aug-inclusive value 0.475 [0.399, 0.542] at n=9 (incl. 3 Finding L aug variants) |
| **Bimodal split** | High-cluster (pure-text / single-output) F1 ≥ 0.95; low-cluster (CLI-wrappers) F1 < 0.10. Mann-Whitney p=0.030. |
| **LLM vs static regex** | 2.5× recall asymmetry (0.682 vs 0.273); McNemar p=0.003, Wilcoxon p=0.047 on n=11 incl. aug variants. Production-only n=8 gives McNemar's p≈0.125 (not significant at α=0.05); the recall gap is directionally consistent in both samples. |
| **Cross-LLM stability** | Hosts Jaccard between Claude Opus 4.7 and OpenAI Codex predictors: **0.41–0.43** (fresh-Claude↔Codex 0.41, orig-Claude↔Codex 0.43). LLM-of-prediction is a load-bearing methodological parameter. |
| **Adversarial defense-in-depth** | 6/6 attack mutations contained by composition (L1 5/6=83%, L2 4/6=67%, L3+L4 6/6=100% each). L1 brittleness drops to 0% under realistic minimal regex (per `analysis/mutation-suite-ablation.md`). |
| **Constructive direction** | SKILL.md → egress allowlist admits **77% of legitimate observed traffic** and flags **50% as undeclared** on the 8-skill subset with non-empty network surface. |

---

## Where to start

Read in this order (≈30 min total):

1. **[`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)** — one-page TL;DR with task framing, headline numbers, five strongest findings, constructive answer to the research question.
2. **[`report.pdf`](report.pdf)** (or **[`report.html`](report.html)** / **[`report.md`](report.md)** for source) — final report, ≈14 PDF pages, 9 sections + abstract, 6 embedded figures. Section 5 catalogues findings A–O; §6 + §6.1 develop the SKILL.md → policy direction; §8 maps onto Professor Monperrus's three subgoals (capability-based permissions, sandboxing-granularity, static + semantic detection); §8.1 documents challenges and corrections.
3. **[`presentation/`](presentation/)** — the KTH ASSERT lightning-talk deck (2026-05-18). Live at [sirray03.github.io/agentic-skill-behavioral-audit/talk/](https://sirray03.github.io/agentic-skill-behavioral-audit/talk/) or open [`presentation/slides.html`](presentation/slides.html) locally. Reveal.js, 11 main + 6 backup slides, self-contained.
4. **[`SKILL_AUTHORING_GUIDE.md`](SKILL_AUTHORING_GUIDE.md)** — community-facing six-practice checklist for skill maintainers, derived empirically from the audit. Three-page artefact for the agentic-skills ecosystem rather than the academic reviewer.
5. **[`methodology.md`](methodology.md)** — synthesised methodology spine (sample design, harness, prediction step, comparison metrics, blind spots, simplifications).
6. **[`DECISIONS.md`](DECISIONS.md)** — chronological log of the design decisions that landed where they did, including the major pivots (Docker → WSL2, n=15 → n=25, the 256× write-ratio mechanism investigation, the L1 100%→83% correction).

---

## Repository layout

```
agentic-skill-behavioral-audit/
├── README.md                          # ← you are here
├── report.md / report.html            # final report (9 sections + 6 figures)
├── EXECUTIVE_SUMMARY.md               # 1-page TL;DR
├── SKILL_AUTHORING_GUIDE.md           # community-facing six-practice checklist
├── methodology.md                     # synthesised methodology spine
├── DECISIONS.md                       # chronological design-decision log
├── manifest.csv                       # machine-readable skill inventory
├── LICENSE                            # MIT
│
├── skills/                            # 25 production + 1 adversarial + 6 mutations + 3 augmented
│   └── <skill-id>/
│       ├── SKILL.md                   # verbatim from upstream maker repo (2026-05-07 / 2026-05-09)
│       ├── task.md                    # representative-invocation prompt (drawn from maker docs)
│       ├── prediction.json            # canonical Claude Opus 4.7 xhigh prediction
│       ├── prediction-fresh.json      # clean-home Claude (cross-LLM-variance comparison)
│       ├── prediction-codex.json      # OpenAI Codex CLI (cross-LLM)
│       ├── prediction-default.json    # archived early default-effort baseline
│       ├── trace.json                 # canonical orig-Claude high-effort runtime trace
│       ├── trace-codex.json           # cross-agent Codex variant (7 skills)
│       ├── trace-realcreds.json       # real-creds variant (3 skills)
│       ├── trace-k-rep{1,2}.json      # repeat-invocation stability (3 skills × 2 reps)
│       ├── trace-n-{medium,xhigh}.json # runtime-effort sensitivity (3 skills × 2 efforts)
│       ├── trace-l-{alt1,alt2}.json   # multi-task fuzzing (3 skills × 2 alternates)
│       └── skill-policy.json          # registry-deployable policy bundle (5 examples)
│
├── analysis/                          # 18 narrative .md docs + paired structured JSON + analysis scripts
│   ├── compare.py / summary.{json,md} / per-skill.json
│   ├── stats.py / stats.{json,md}                    # bootstrap CIs + McNemar's + Wilcoxon
│   ├── static-audit.py / static-vs-dynamic.md        # regex baseline (recall 0.27 vs LLM 0.68)
│   ├── policy-eval.py / policy-eval.{json,md}        # SKILL.md → egress allowlist eval
│   ├── policy-enforcement.py / policy-enforcement.md # iptables-in-netns deployment recipe
│   ├── policy-bundle-generator.py / policy-bundle-prototype.md # registry-deployable bundle
│   ├── mutation-suite.py / mutation-suite.md         # 6×4 detection-rate table
│   ├── mutation-suite-ablation.py / mutation-suite-ablation.md # L1 brittleness ablation
│   ├── failure-mode-taxonomy.py / failure-mode-taxonomy.md # 24 hosts × 7 categories
│   ├── predictor-variance.py / predictor-variance.{json,md}
│   ├── predictor-vs-truth.py / predictor-vs-truth.{json,md}
│   ├── subgroup-analysis.py / subgroup-analysis.{json,md}
│   ├── stability-effort.py / stability-effort.{json,md}
│   ├── multitask-fuzzing.py / multitask-fuzzing.{json,md}
│   ├── sandboxing-granularity.py / sandboxing-granularity.{json,md}
│   ├── adversarial-policy-interaction.py / finding-o-adversarial-policy.md
│   ├── mechanism-investigation.md                    # 256× write-ratio decomposition
│   ├── citation-justifications.md                    # per-citation credibility record
│   └── figures.py                                    # generates the 6 SVG/PNG visualisations
│
├── figures/                           # 6 figures (PNG + SVG): F1 distribution, predictor variance,
│                                      #   pred-vs-obs scatter, CI forest, failure modes, mutation suite
│
├── harness/                           # WSL2 setup + run scripts + parsers
│   ├── setup-skills.sh                # apt + npm + pip install + per-CLI auth setup
│   ├── predict.py                     # P3 — claude -p with structured-JSON output
│   ├── predict-codex.py               # cross-LLM Codex variant
│   ├── run-skill.sh                   # P4 — strace + tcpdump + claude -p, 15-min timeout
│   ├── run-skill-codex.sh             # cross-agent variant
│   ├── parse-strace.py / parse-pcap.py # raw → structured JSON
│   └── md-to-html.py                  # report.md → report.html with embedded CSS
│
├── skill-auditor/                     # pip-installable CLI distillation
│   ├── pyproject.toml
│   ├── README.md
│   └── skill_auditor/                 # predict / audit / policy subcommands
│
├── dashboard/                         # Astro static site (companion interactive view)
│   ├── README.md                      # dashboard build + deploy notes
│   ├── astro.config.mjs / package.json
│   ├── public/                        # static assets
│   ├── scripts/                       # pre-build data extraction
│   └── src/                           # Astro components, content collections, layouts
│
└── presentation/                      # KTH ASSERT lightning-talk deck (2026-05-18)
    ├── README.md                      # deck contents + structure + reproduction notes
    ├── slides.html                    # self-contained Reveal.js deck — 11 main + 6 backup
    ├── figures/                       # the six audit figures + per-slide screenshots
    └── scripts/                       # Playwright dashboard-screenshot capture + overflow checker
```

---

## Reproducing the work

### Prerequisites

- **Linux environment** (WSL2 Kali Linux Rolling 2024.4 was used for the original work; any modern Linux with `strace`, `tcpdump`, `python3`, `node`, `npm`, `pip` should work).
- **Claude Code CLI** (oauth-authenticated subscription, no API key required). Install: `npm install -g @anthropic-ai/claude-code`.
- **OpenAI Codex CLI** (for cross-agent / cross-LLM variants). Install: `npm install -g @openai/codex`.
- **Capability grants** for `tcpdump` so it runs without sudo: `sudo setcap cap_net_raw,cap_net_admin+eip $(which tcpdump)`.

### Re-run the harness on a single skill

```bash
# (1) install all 25 skills + their wrapped CLIs into ~/.claude/skills/ + system PATH
bash harness/setup-skills.sh

# (2) re-run prediction step on one skill
python3 harness/predict.py skills/wrangler/SKILL.md > /tmp/pred.json

# (3) re-run instrumented invocation
SKILL_ID=wrangler bash harness/run-skill.sh
# outputs go to skills/wrangler/{trace,raw,claude-stdout}.{json,log}

# (4) re-run comparison
python3 analysis/compare.py
# produces analysis/{summary,per-skill}.json + analysis/summary.md

# (5) regenerate figures
python3 analysis/figures.py
```

### Use the pip-installable CLI on a new SKILL.md

```bash
cd skill-auditor && pip install -e .

# Predict capability footprint from SKILL.md alone
skill-auditor predict path/to/SKILL.md --predictor claude --effort xhigh

# Full audit (predict + instrument + compare)
skill-auditor audit path/to/SKILL.md --task "your representative invocation prompt" --out /tmp/audit/

# Generate registry-deployable policy bundle
skill-auditor policy path/to/SKILL.md --out /tmp/skill-policy.json
```

The pip package is the deployable distillation of the n=25 methodology — three subcommands (`predict` / `audit` / `policy`) wrapping the same instrumentation pipeline this repository documents.

### Build and run the dashboard locally

```bash
cd dashboard
npm install
npm run dev    # http://localhost:4321
```

The dashboard is an Astro static site that consumes `../skills/`, `../analysis/`, `../report.md`, and the figures at build time. Suitable for GitHub Pages deployment from this repository (the dashboard's `npm run build` produces a static `dist/` folder).

---

## Headline visualizations

The six figures embedded in the report tell the empirical story at a glance. All under `figures/` as both SVG (vector, print-ready) and PNG (raster, 200 DPI):

| | |
|---|---|
| **Figure 1** | Per-skill paths_read F1 sorted ascending — bimodal distribution, Mann-Whitney p=0.030 |
| **Figure 2** | Pairwise Jaccard heatmap across three predictor sources (orig-Claude, fresh-Claude, Codex) |
| **Figure 3** | Predicted vs observed host count scatter — points above the y=x diagonal are the under-prediction regime |
| **Figure 4** | Headline aggregate F1 + cross-LLM Jaccard with bootstrap 95% CIs (forest plot) |
| **Figure 5** | Failure-mode taxonomy: 24 hosts × 7 categories, declared vs undeclared per-skill |
| **Figure 6** | Mutation × defense-layer detection-rate (6×4 heatmap) — defense-in-depth visualization |

---

## What this work is *not*

- **Not a registry-scale empirical study** — Liu et al. and Socket cover that ground at n=42k+ and n=60k+ respectively. This work covers n=25 in instrumentation depth.
- **Not a deployed-tooling release** — the pip CLI is research code, not a production-hardened audit tool. The `skill-policy.json` bundle is a prototype, not an enforcement-ready artefact.
- **Not a replacement for static scanners** — the four-layer defense stack (regex / LLM-semantic / runtime / threat-intel-deny-overlay) explicitly composes static and dynamic; the 6/6 mutation-suite coverage *requires* the composition. See report §5.4 + 5.7.
- **Not exhaustive** — section 7 (Limits) and section 8.1 (Challenges and corrections) document what the harness systematically misses (TLS payloads, agent-tool-mediated IO, async post-task callbacks, mmap-only IO) and what I would do differently with two more weeks.

---

## Citation

If this work is useful for your research:

```bibtex
@misc{putra2026agenticskillaudit,
  author       = {Putra, Rayhan},
  title        = {A Dynamic Behavioural Auditor for Agentic Skills},
  year         = {2026},
  month        = {May},
  howpublished = {\url{https://github.com/SirRay03/agentic-skill-behavioral-audit}},
  note         = {Programming exercise for KTH ASSERT (Professor Monperrus); n=25 agentic skills with full strace + tcpdump instrumentation, mutation-suite defense-in-depth evaluation, and SKILL.md \(\rightarrow\) policy generator.}
}
```

## License

MIT — see [`LICENSE`](LICENSE). Verbatim third-party SKILL.md files under `skills/<id>/SKILL.md` retain their original upstream licensing; see `manifest.csv` for the per-skill upstream URL and check the upstream repository for the canonical license. The instrumentation, analysis code, report text, and dashboard are MIT.

## Author

**Rayhan Putra** · Bandung Institute of Technology STI 2021 (BSc Cum Laude, 3.59/4.00) · KTH MSc Cybersecurity Autumn 2026 admit · `rayhansiregar03@gmail.com` · [github.com/SirRay03](https://github.com/SirRay03) · [linkedin.com/in/rayhansiregar](https://linkedin.com/in/rayhansiregar)

This work was conducted as the entry-point evaluation for a 4-month, 25%-FTE remote research-engineering role under Professor Monperrus (KTH ASSERT) on the open thesis topic *"Automatic Hardening of Agentic Skills"*.
