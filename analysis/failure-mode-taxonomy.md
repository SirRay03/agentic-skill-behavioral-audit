# Phase 1.F — Network-Gap Failure-Mode Taxonomy

Total distinct skill-attributable observed hosts (across all traces): **24**

## Counts per category — declared vs undeclared

*'Declared' = the host is present in at least one of the three predictor outputs
(orig-Claude, fresh-Claude, Codex), under suffix-aware predicate matching.
'Undeclared' = absent from all three.*

| Category | Total observed | Declared by ≥1 predictor | Undeclared by all 3 |
|---|---|---|---|
| telemetry-beacon | 3 | 2 | 1 |
| binary-fetch-CDN | 5 | 2 | 3 |
| post-auth-API | 3 | 3 | 0 |
| runtime-config-probe | 6 | 1 | 5 |
| pkg-registry | 1 | 1 | 0 |
| auth-token-exchange | 3 | 1 | 2 |
| external-target | 3 | 1 | 2 |
| **Total** | **24** | **11** | **13** |

## Per-host detail

| Host | Category | Declared by | n traces | Why |
|---|---|---|---|---|
| `accounts.google.com` | auth-token-exchange | **none (Finding C/G)** | 1 | Google OAuth account endpoint |
| `add-skill.vercel.sh` | binary-fetch-CDN | **none (Finding C/G)** | 1 | skills.sh installer dispatch (returns install scripts/binaries) |
| `android.clients.google.com` | runtime-config-probe | **none (Finding C/G)** | 1 | Chromium platform config probe |
| `api.firecrawl.dev` | post-auth-API | codex,fresh,orig | 1 | Firecrawl scrape API, requires FIRECRAWL_API_KEY |
| `clients2.google.com` | runtime-config-probe | **none (Finding C/G)** | 1 | Chromium component update check |
| `content-autofill.googleapis.com` | auth-token-exchange | **none (Finding C/G)** | 1 | Chromium autofill API (Google-account scoped) |
| `dist.inference.sh` | binary-fetch-CDN | codex,fresh,orig | 1 | inference.sh CLI binary distribution |
| `firebase-public.firebaseio.com` | runtime-config-probe | fresh,orig | 1 | Firebase Realtime DB public-config startup probe |
| `firebase.googleapis.com` | post-auth-API | codex,fresh,orig | 1 | Firebase Management API (real-creds unlocks) |
| `github.com` | binary-fetch-CDN | fresh | 2 | Code/binary repository (release-asset & raw fetches dispatch through here) |
| `metrics.semgrep.dev` | telemetry-beacon | codex,fresh,orig | 1 | Semgrep usage telemetry, fires per scan |
| `mtalk.google.com` | runtime-config-probe | **none (Finding C/G)** | 1 | Google Cloud Messaging endpoint (Chromium GCM keepalive) |
| `news.ycombinator.com` | external-target | **none (Finding C/G)** | 1 | user-specified scrape target for agent-browser |
| `ogads-pa.clients6.google.com` | telemetry-beacon | **none (Finding C/G)** | 1 | Google Ads/analytics beacon (Chromium-implied) |
| `play.google.com` | runtime-config-probe | **none (Finding C/G)** | 1 | Chromium/Play Services config |
| `raw.githubusercontent.com` | binary-fetch-CDN | **none (Finding C/G)** | 1 | Raw source/binary fetch (web-search inferencesh package) |
| `registry.npmjs.org` | pkg-registry | codex,fresh,orig | 8 | npm package registry |
| `release-assets.githubusercontent.com` | binary-fetch-CDN | **none (Finding C/G)** | 1 | GitHub Releases binary attachments (firebase emulator JARs) |
| `semgrep.dev` | post-auth-API | codex,fresh,orig | 1 | Semgrep rule registry / authenticated lookups |
| `skills.sh` | external-target | codex,fresh,orig | 1 | find-skills user-targeted catalogue host |
| `sparrow.cloudflare.com` | telemetry-beacon | codex,fresh,orig | 3 | Cloudflare wrangler telemetry, fires unconditionally |
| `www.google.com` | external-target | **none (Finding C/G)** | 1 | Chromium default-page navigation |
| `www.googleapis.com` | auth-token-exchange | codex,fresh,orig | 1 | Google API discovery + token exchange |
| `www.gstatic.com` | runtime-config-probe | **none (Finding C/G)** | 1 | Google static assets / Chromium runtime |

## Defense recommendation per category

Different gap classes need different defenses:

| Category | Best defense |
|---|---|
| telemetry-beacon | **Known-suffix deny-overlay** that wins over allowlist wildcards (Finding M). `metrics.*`, `sparrow.*`, `*-telemetry.*` patterns. |
| binary-fetch-CDN | **SLSA / in-toto provenance** check on fetched artifacts; pin to known-hash. Treat as supply-chain risk, not network-policy risk. |
| post-auth-API | **Recoverable via real-creds runs** — already partially demonstrated for firebase. Stub-creds traces are a strict lower bound. |
| runtime-config-probe | **Allow at base policy level** — these are agent-runtime concerns (Chromium, Firebase tools), not skill-specific. |
| pkg-registry | **Allow at base policy level** — `registry.npmjs.org` and equivalents are universal infrastructure. |
| auth-token-exchange | **Allow at base policy level** alongside pkg-registry; tightly scoped per OAuth provider. |
| external-target | **Skill-specific allowlist** — must be admitted because the user is asking the skill to access the target. Pre-deploy review for trust. |

## Implication for Section 5 of the report

The 77% legit-allow / 50% telemetry-catch headline is a sum across these categories;
decomposing reveals where each defense layer pays its way. Specifically:

- **Telemetry-beacons are the only category where the LLM-derived allowlist consistently fails** (because predictors emit wildcard patterns that accidentally match the telemetry subdomain — Finding M). The deny-overlay fixes this without dynamic instrumentation.
- **Binary-fetch-CDNs** are present in the trace but represent supply-chain risk (e.g., a compromised github.com release-asset would deliver malware to firebase-tools), not policy-violation risk. Different defense layer entirely.
- **Post-auth-APIs** are *correctly under-observed* in stub-creds runs; the real-creds variant work showed they unlock under authentication. Lower-bound framing of the trace data is empirically validated.
- **Runtime-config-probes, pkg-registry, auth-token-exchange** belong in an agent-runtime base policy, not in skill-specific allowlists. Putting them in skill-specific allowlists is the source of most false-positive-block events.

This decomposition is the pragmatic recommendation that ships with the SKILL.md → policy generator: the per-skill allowlist should not enumerate hosts that belong in the base policy.
