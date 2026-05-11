# Phase 2.I — Policy Enforcement Simulation

## Setting

For three skills with non-trivial network surface, replay observed connections
against the prediction.json-derived egress allowlist. Classify each host into one
of four cells:

- **ALLOWED-LEGIT** — host is on allowlist, host is legitimate skill IO. Good.
- **ALLOWED-TELEMETRY** — host is on allowlist (typically via wildcard), but is vendor telemetry. Bad — Finding M (wildcard sabotage).
- **BLOCKED-LEGIT** — host is NOT on allowlist but is load-bearing for the skill's documented happy path. Bad — policy breaks the task.
- **BLOCKED-UNDECLARED** — host is NOT on allowlist and is undocumented telemetry/runtime/etc. Good — policy correctly blocks Finding C/G.

Then check whether the agent self-reported task completion in `claude-stdout.json`
to compare *actual* outcome (no enforcement) vs. *would-have-been* outcome under
enforcement.

## Results — three skills

### wrangler (trace: trace-realcreds.json)

- **Predicted allowlist** (6): `['developers.cloudflare.com', 'api.cloudflare.com', '*.cloudflare.com', 'registry.npmjs.org', 'workers.cloudflare.com', '*.workers.dev']`
- **Observed skill-attributable hosts**: ['sparrow.cloudflare.com']

| Host | Classification |
|---|---|
| `sparrow.cloudflare.com` | ⚠ ALLOWED-TELEMETRY |

- ALLOWED-LEGIT: 0
- ALLOWED-TELEMETRY: 1 (Finding M)
- BLOCKED-LEGIT: 0 (would break task)
- BLOCKED-UNDECLARED: 0 (telemetry correctly caught)

**Predicted enforcement outcome**: WOULD COMPLETE
**Agent's actual outcome (no enforcement)**: completed

> Agent's self-report: *Dry-run succeeded. The worker bundle validates cleanly:

- `worker/wrangler.jsonc` — minimal config (name, main, compatibility_date 2026-01-01)
- `worker/src/index.ts` — basic fetch handler returning "Hello, World!"
- Bundle size: 0.18 KiB, no bindings*

### firebase-hosting-basics (trace: trace-realcreds.json)

- **Predicted allowlist** (7): `['firebase.tools', 'registry.npmjs.org', '*.firebaseio.com', '*.googleapis.com', '*.firebaseapp.com', '*.web.app', 'localhost']`
- **Observed skill-attributable hosts**: ['firebase.googleapis.com', 'registry.npmjs.org', 'www.googleapis.com']

| Host | Classification |
|---|---|
| `firebase.googleapis.com` | ✓ ALLOWED-LEGIT |
| `registry.npmjs.org` | ✓ ALLOWED-LEGIT |
| `www.googleapis.com` | ✓ ALLOWED-LEGIT |

- ALLOWED-LEGIT: 3
- ALLOWED-TELEMETRY: 0 (Finding M)
- BLOCKED-LEGIT: 0 (would break task)
- BLOCKED-UNDECLARED: 0 (telemetry correctly caught)

**Predicted enforcement outcome**: WOULD COMPLETE
**Agent's actual outcome (no enforcement)**: completed

> Agent's self-report: *Emulator started successfully. Summary:

**Project layout** at `./fb-test/`:
- `public/index.html` — "Hello World" page
- `firebase.json` — hosting config (public dir = `public`)
- `.firebaserc` — default project `demo-test`

**Emulator startup output** (cleaned of spinner/ANSI):

```
i  emulators: Starting emulators: hosting
i  emulators: Detected demo project ID "demo-test", emulated services will use a demo configuration...
i  hosting[demo-test]: Serving hosting files from: public
✔  hosting[*

### firecrawl-scrape (trace: trace-realcreds.json)

- **Predicted allowlist** (2): `['api.firecrawl.dev', '*']`
- **Observed skill-attributable hosts**: ['api.firecrawl.dev']

| Host | Classification |
|---|---|
| `api.firecrawl.dev` | ✓ ALLOWED-LEGIT |

- ALLOWED-LEGIT: 1
- ALLOWED-TELEMETRY: 0 (Finding M)
- BLOCKED-LEGIT: 0 (would break task)
- BLOCKED-UNDECLARED: 0 (telemetry correctly caught)

**Predicted enforcement outcome**: WOULD COMPLETE
**Agent's actual outcome (no enforcement)**: completed

> Agent's self-report: *Saved to `./.firecrawl/page.md` (5 lines, main content only).*

## Summary verdict

| Skill | Predicted enforcement outcome | Agent actual outcome | Telemetry caught | Telemetry slipped through |
|---|---|---|---|---|
| wrangler | WOULD COMPLETE | completed | 0 | 1 |
| firebase-hosting-basics | WOULD COMPLETE | completed | 0 | 0 |
| firecrawl-scrape | WOULD COMPLETE | completed | 0 | 0 |

## Live deployment recipe (deferred — Linux container required)

The simulation above replays connections against the allowlist policy. To actually
enforce the policy at runtime — the gold-standard 'does it actually work' test —
deploy the per-skill allowlist as kernel-level egress filtering. The cleanest setup:

```bash
# 1. Generate per-skill iptables rules from prediction.json
python3 -c "
import json, socket
pred = json.load(open('skills/wrangler/prediction.json'))
ips = set()
for host in pred['hosts']:
    if host.startswith('*'): continue  # wildcard predicates need DNS-aware filtering
    try: ips.update(ai[4][0] for ai in socket.getaddrinfo(host, None))
    except socket.gaierror: pass
for ip in ips: print(f'-A OUTPUT -d {ip} -j ACCEPT')
print('-A OUTPUT -j DROP')
" > /tmp/skill-policy.rules

# 2. Apply in a network namespace (root required for iptables)
sudo unshare -n bash <<'BWRAP'
ip link set lo up
iptables-restore < /tmp/skill-policy.rules
su -c 'bash harness/run-skill.sh wrangler' user
BWRAP
```

Why this requires root: iptables rules manipulate kernel netfilter tables, which
are root-only even inside a namespace (because user namespaces don't grant CAP_NET_ADMIN
to kernel netfilter). On a CI/CD or production agent harness deployment, root is
available; in our WSL2-direct development sandbox we elect not to take root, so the
simulation is the closest proxy.

DNS-aware filtering (for wildcard predicates like `*.cloudflare.com`) requires either:
- (a) Resolving the wildcard to specific subdomains via authoritative DNS query and
      adding per-subdomain rules — fragile, subdomains can change
- (b) Running a DNS-aware filter like dnsmasq with allowlist subdomains, then iptables
      rules pointing at the resolved IPs.

## Headline finding

Across the three test skills, the SKILL.md-derived allowlist would have been
**non-task-breaking** for 3/3 skills under enforcement (no BLOCKED-LEGIT cells), caught 0 undeclared/telemetry hosts cleanly, and let 1 ALLOWED-TELEMETRY slip through (wildcard sabotage, Finding M).

The simulation outcome aligns with the constructive answer in Section 6 of the report:
the SKILL.md-derived policy is empirically sufficient for honest-maintainer skills,
with the wildcard-deflation post-process from Finding M as the necessary follow-up to
close the ALLOWED-TELEMETRY cell.
