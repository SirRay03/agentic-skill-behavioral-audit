"""LLM-prediction wrapper. Mirrors kth-skill-audit-exercise/harness/predict.py's
prompt template + JSON-extraction logic but exposes them as importable
functions for the CLI."""
from __future__ import annotations
import json
import os
import re
import subprocess


PROMPT_TEMPLATE = """You are predicting the runtime capability footprint of an "agentic skill" from its SKILL.md text alone.

Below is the verbatim SKILL.md for a skill called "{skill_id}". A coding agent loaded with this skill, given a representative task that exercises the skill's primary verb, will perform some combination of: filesystem reads, filesystem writes, filesystem deletions, network connections, and subprocess invocations.

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
- Items in BOTH paths_read and paths_written if the skill modifies a config file
- Hosts: list declared API endpoints AND third-party hosts implied by the skill's verbs
- If pure prose with no IO, return empty arrays except rationale

SKILL.md:
---
{skill_md}
---

Output the JSON object only. No prose, no markdown fence, just the raw JSON."""


def build_prompt(*, skill_id: str, skill_md: str) -> str:
    return PROMPT_TEMPLATE.format(skill_id=skill_id, skill_md=skill_md)


def call_predictor(prompt: str, *, agent: str = "claude", effort: str = "xhigh",
                   timeout: int = 300) -> tuple[str, str, int]:
    """Run the predictor (claude or codex) non-interactively. Returns
    (stdout, stderr, exit_code)."""
    if agent == "claude":
        cmd = [
            "claude", "-p", prompt,
            "--dangerously-skip-permissions",
            "--output-format", "text",
            "--no-session-persistence",
            "--disable-slash-commands",
            "--effort", effort,
        ]
    elif agent == "codex":
        cmd = [
            "codex", "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            prompt,
        ]
    else:
        raise ValueError(f"unknown agent: {agent}")

    result = subprocess.run(
        cmd,
        input="",
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ.copy(),
    )
    return result.stdout.strip(), result.stderr, result.returncode


def extract_json(text: str) -> dict | None:
    """Find a JSON object in stdout, even if wrapped in prose or fenced."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    candidates = sorted(
        (m.group(0) for m in re.finditer(r"\{[\s\S]*?\}", text)),
        key=len, reverse=True,
    )
    for c in candidates:
        try:
            d = json.loads(c)
            if isinstance(d, dict) and "rationale" in d:
                return d
        except json.JSONDecodeError:
            continue
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
