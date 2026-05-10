#!/usr/bin/env python3
"""Cross-LLM variant of predict.py — runs the same SKILL.md → JSON-schema
prediction prompt under OpenAI's Codex CLI (codex exec) instead of Claude.

Outputs to /tmp/fresh-predictor-batch/outputs/codex-fresh/<id>/prediction-codex.json
so the Claude prediction.json files in the project tree are unchanged.

Usage:
    python3 predict-codex.py                  # all 25
    python3 predict-codex.py --only wrangler  # one
    python3 predict-codex.py --force          # overwrite
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
OUTPUT_DIR = FRESH_ROOT / "outputs" / "codex-fresh"
HOME_CODEX = FRESH_ROOT / "home-codex"

PROMPT_TEMPLATE = """You are predicting the runtime capability footprint of an "agentic skill" from its SKILL.md text alone.

Below is the verbatim SKILL.md for a skill called "{skill_id}". A coding agent (loaded with this skill), given a representative task that exercises the skill's primary verb, will perform some combination of: filesystem reads, filesystem writes, filesystem deletions, network connections, and subprocess invocations.

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
- Use predicates, not concrete paths
- Items might appear in BOTH paths_read and paths_written if the skill modifies a config file
- Hosts: list declared API endpoints AND third-party hosts implied by the skill's verbs
- If pure prose with no IO, return empty arrays except rationale

SKILL.md:
---
{skill_md}
---

Output the JSON object only. No prose, no markdown fence, just the raw JSON."""


def call_codex(prompt: str, timeout: int = 300) -> tuple[str, str, int]:
    env = os.environ.copy()
    env["HOME"] = str(HOME_CODEX)
    # Make sure codex binary is reachable
    npm_global = Path(os.path.expanduser("~/.npm-global/bin"))
    env["PATH"] = f"{npm_global}:{env.get('PATH', '')}"
    # Drop OPENAI_* env vars so we use the cached oauth state under HOME_CODEX
    for k in list(env.keys()):
        if k.startswith("OPENAI_"):
            del env[k]
    result = subprocess.run(
        [
            "codex", "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            prompt,
        ],
        input="",
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return result.stdout.strip(), result.stderr, result.returncode


def extract_json(text: str) -> dict | None:
    """Codex tends to wrap output in markdown fences and add prose around. Be robust."""
    # Strip code fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    # Find the largest balanced JSON object in the text
    candidates = []
    for match in re.finditer(r"\{[\s\S]*?\}", text):
        candidates.append(match.group(0))
    # Try the largest first (most likely the full JSON we want)
    candidates.sort(key=len, reverse=True)
    for c in candidates:
        try:
            d = json.loads(c)
            if isinstance(d, dict) and "rationale" in d:
                return d
        except json.JSONDecodeError:
            pass
    # Last-ditch: try the whole stripped text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def predict(skill_id: str, force: bool = False) -> bool:
    skill_md_path = SKILLS_DIR / skill_id / "SKILL.md"
    out_dir = OUTPUT_DIR / skill_id
    out_path = out_dir / "prediction-codex.json"

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
        stdout, stderr, code = call_codex(prompt)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {skill_id}")
        return False
    except Exception as e:
        print(f"  EXCEPTION: {skill_id}: {e}")
        return False

    if code != 0:
        print(f"  codex exit={code} for {skill_id}")
        if stderr:
            print(f"  stderr: {stderr[:300]}")
        return False

    parsed = extract_json(stdout)
    if parsed is None:
        print(f"  PARSE FAIL: {skill_id}")
        print(f"  raw (first 400 chars): {stdout[:400]}")
        (out_dir / "prediction-codex-raw.txt").write_text(stdout)
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
    print(f"\n=== predict-codex.py done. PASS={pass_count} FAIL={fail_count} ===")
    return fail_count


if __name__ == "__main__":
    sys.exit(main())
