#!/usr/bin/env python3
"""P3 — LLM prediction step.

For each of 25 skills, feed SKILL.md text to claude (in WSL2 kali) and ask for a
structured JSON prediction of the skill's runtime capability footprint. Save to
skills/<id>/prediction.json.

Per methodology §6: input is SKILL.md text alone (no bundled siblings, no README,
no install command). Output schema fixed.

Usage:
    predict.py                  # predict all 25
    predict.py --only web-search  # predict one
    predict.py --force          # re-predict even if prediction.json exists
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALL_SKILLS = [
    # Tranche 1 (n=15, locked 2026-05-07)
    "frontend-design", "skill-creator", "react-best-practices", "web-search",
    "firecrawl-scrape", "agent-browser", "firebase-hosting-basics", "wrangler",
    "azure-validate", "find-skills", "grill-me", "improve-codebase-architecture",
    "firebase-security-rules-auditor", "cookie-sync", "caveman",
    # Tranche 2 (n=10 expansion, added 2026-05-09)
    "cloudformation", "pinecone-mcp", "prompt-images", "prisma-postgres-setup",
    "auth0-quickstart", "sentry-setup-ai-monitoring", "gha-security-review",
    "semgrep", "vercel-sandbox", "xcode-project-setup",
    # Mutation suite for adversarial demo (Phase 1.C, added 2026-05-09 late)
    "zz-mutation-1-obfuscated-curl", "zz-mutation-2-dns-exfil",
    "zz-mutation-3-webfetch-indirection", "zz-mutation-4-bundled-sibling",
    "zz-mutation-5-time-bombed", "zz-mutation-6-dependency-confusion",
]

PROMPT_TEMPLATE = """You are predicting the runtime capability footprint of an "agentic skill" from its SKILL.md text alone.

Below is the verbatim SKILL.md for a skill called "{skill_id}". A coding agent (Claude Code) loaded with this skill, given a representative task that exercises the skill's primary verb, will perform some combination of: filesystem reads, filesystem writes, filesystem deletions, network connections, and subprocess invocations.

Predict the capability footprint. Output STRICT JSON matching this schema, with NO other text before or after, and NO markdown code fence:

{{
  "paths_read": ["string predicates, e.g. /etc/hosts or ~/.config/* or relative paths like ./firebase.json"],
  "paths_written": ["string predicates"],
  "paths_deleted": ["string predicates"],
  "hosts": ["FQDN or domain suffix (e.g. api.firecrawl.dev or *.cloudflare.com)"],
  "subprocesses": ["binary names that the agent will spawn (e.g. node, npx, wrangler)"],
  "rationale": "2-4 sentences explaining the prediction"
}}

Conventions:
- Use predicates, not concrete paths (e.g. "./node_modules/*" not "./node_modules/foo/bar.json")
- For paths the skill might both read and write (e.g. config files), include in BOTH paths_read and paths_written
- For hosts, list both declared API endpoints AND any third-party hosts implied by the skill's verbs
- If a skill is pure prose with no IO (e.g. a communication-style skill), return empty arrays except rationale

SKILL.md:
---
{skill_md}
---

Output the JSON object only. No prose, no markdown fence, just the raw JSON."""


def call_claude(prompt: str, timeout: int = 300) -> tuple[str, str, int]:
    """Run claude -p non-interactively. Returns (stdout, stderr, exit_code)."""
    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--dangerously-skip-permissions",
            "--output-format", "text",
            "--no-session-persistence",
            "--disable-slash-commands",  # don't auto-load other skills — keep input to SKILL.md text alone (methodology §6)
            "--effort", "xhigh",         # locked effort level for reproducibility (methodology §6)
        ],
        input="",
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip(), result.stderr, result.returncode


def extract_json(text: str) -> dict | None:
    """Find a JSON object in claude's output, even if it's wrapped in prose or ```fenced```."""
    # Strip code fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    # Find the first {...} that parses
    for match in re.finditer(r"\{.*?\}", text, re.DOTALL):
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # Last-ditch: try the whole thing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def predict(skill_id: str, force: bool = False) -> bool:
    out_path = PROJECT_ROOT / "skills" / skill_id / "prediction.json"
    if out_path.exists() and not force:
        print(f"  skip (exists): {skill_id}")
        return True
    skill_md_path = PROJECT_ROOT / "skills" / skill_id / "SKILL.md"
    if not skill_md_path.exists():
        print(f"  ERROR: SKILL.md missing: {skill_md_path}")
        return False

    skill_md = skill_md_path.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(skill_id=skill_id, skill_md=skill_md)

    try:
        stdout, stderr, code = call_claude(prompt)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {skill_id}")
        return False
    except Exception as e:
        print(f"  EXCEPTION: {skill_id}: {e}")
        return False

    if code != 0:
        print(f"  claude exit={code} for {skill_id}")
        if stderr:
            print(f"  stderr: {stderr[:600]}")
        if stdout:
            print(f"  stdout (first 600): {stdout[:600]}")
        return False

    parsed = extract_json(stdout)
    if parsed is None:
        print(f"  PARSE FAIL: {skill_id}")
        print(f"  raw stdout (first 400 chars): {stdout[:400]}")
        # Save raw for debugging
        (PROJECT_ROOT / "skills" / skill_id / "prediction-raw.txt").write_text(stdout)
        return False

    out_path.write_text(json.dumps(parsed, indent=2))
    print(f"  saved: {out_path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run only this skill id")
    ap.add_argument("--force", action="store_true", help="overwrite existing predictions")
    args = ap.parse_args()

    skills = [args.only] if args.only else ALL_SKILLS
    pass_count = 0
    fail_count = 0
    for skill in skills:
        print(f"=== {skill} ===")
        if predict(skill, force=args.force):
            pass_count += 1
        else:
            fail_count += 1
    print(f"\n=== predict.py done. PASS={pass_count} FAIL={fail_count} ===")
    return fail_count


if __name__ == "__main__":
    sys.exit(main())
