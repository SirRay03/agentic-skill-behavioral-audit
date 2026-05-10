#!/usr/bin/env python3
"""Fresh-session variant of predict.py — runs each prediction with HOME
pointed at /tmp/fresh-predictor-batch/home-claude so no auto-memory, plugins,
or skills under ~/.claude/ leak into the prediction context.

Outputs to /tmp/fresh-predictor-batch/outputs/claude-fresh/<id>/prediction-fresh.json
so the original prediction.json is preserved in the project tree.

Usage:
    python3 predict-fresh.py                  # all 25
    python3 predict-fresh.py --only wrangler  # one
    python3 predict-fresh.py --force          # overwrite
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

FRESH_ROOT = Path(os.environ.get("FRESH", "/tmp/fresh-predictor-batch"))
SKILLS_DIR = FRESH_ROOT / "skills"
OUTPUT_DIR = FRESH_ROOT / "outputs" / "claude-fresh"
HOME_CLAUDE = FRESH_ROOT / "home-claude"

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


def call_claude_fresh(prompt: str, timeout: int = 300) -> tuple[str, str, int]:
    env = os.environ.copy()
    env["HOME"] = str(HOME_CLAUDE)
    # Drop anything related to other user-level claude state
    for k in list(env.keys()):
        if k.startswith(("CLAUDE_", "ANTHROPIC_")):
            del env[k]
    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--dangerously-skip-permissions",
            "--output-format", "text",
            "--no-session-persistence",
            "--disable-slash-commands",
            "--effort", "xhigh",
        ],
        input="",
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return result.stdout.strip(), result.stderr, result.returncode


def extract_json(text: str) -> dict | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    for match in re.finditer(r"\{.*?\}", text, re.DOTALL):
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def predict(skill_id: str, force: bool = False) -> bool:
    skill_md_path = SKILLS_DIR / skill_id / "SKILL.md"
    out_dir = OUTPUT_DIR / skill_id
    out_path = out_dir / "prediction-fresh.json"

    if not skill_md_path.exists():
        print(f"  ERROR: SKILL.md missing: {skill_md_path}")
        return False
    if out_path.exists() and not force:
        print(f"  skip (exists): {skill_id}")
        return True

    out_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_md_path.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(skill_id=skill_id, skill_md=skill_md)

    try:
        stdout, stderr, code = call_claude_fresh(prompt)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {skill_id}")
        return False
    except Exception as e:
        print(f"  EXCEPTION: {skill_id}: {e}")
        return False

    if code != 0:
        print(f"  claude exit={code} for {skill_id}")
        if stderr:
            print(f"  stderr: {stderr[:300]}")
        return False

    parsed = extract_json(stdout)
    if parsed is None:
        print(f"  PARSE FAIL: {skill_id}")
        print(f"  raw: {stdout[:400]}")
        (out_dir / "prediction-fresh-raw.txt").write_text(stdout)
        return False

    out_path.write_text(json.dumps(parsed, indent=2))
    print(f"  saved: {out_path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run only this skill id")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not SKILLS_DIR.exists():
        print(f"FRESH dir not initialised: {FRESH_ROOT}\nRun harness/setup-fresh-session.sh first.")
        return 1

    skills = [args.only] if args.only else sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir())
    pass_count = 0
    fail_count = 0
    for skill in skills:
        print(f"=== {skill} ===")
        if predict(skill, force=args.force):
            pass_count += 1
        else:
            fail_count += 1
    print(f"\n=== predict-fresh.py done. PASS={pass_count} FAIL={fail_count} ===")
    return fail_count


if __name__ == "__main__":
    sys.exit(main())
