"""Command-line entry point for the skill-auditor toolkit."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from . import __version__
from .predict import call_predictor, build_prompt, extract_json
from .policy import build_policy_bundle


def cmd_predict(args: argparse.Namespace) -> int:
    """skill-auditor predict <SKILL.md> [--effort xhigh] [--out prediction.json]"""
    skill_md_path = Path(args.skill_md)
    if not skill_md_path.exists():
        print(f"error: SKILL.md not found: {skill_md_path}", file=sys.stderr)
        return 1
    skill_md = skill_md_path.read_text(encoding="utf-8")
    skill_id = args.skill_id or skill_md_path.parent.name

    prompt = build_prompt(skill_id=skill_id, skill_md=skill_md)
    stdout, stderr, code = call_predictor(
        prompt, agent=args.agent, effort=args.effort, timeout=args.timeout
    )
    if code != 0:
        print(f"error: predictor exited {code}", file=sys.stderr)
        if stderr:
            print(f"stderr: {stderr[:600]}", file=sys.stderr)
        return code

    parsed = extract_json(stdout)
    if parsed is None:
        print(f"error: could not parse JSON from predictor output", file=sys.stderr)
        print(f"raw stdout (first 600 chars): {stdout[:600]}", file=sys.stderr)
        return 2

    out_path = Path(args.out) if args.out else skill_md_path.parent / "prediction.json"
    out_path.write_text(json.dumps(parsed, indent=2))
    print(f"wrote {out_path}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """skill-auditor audit <SKILL.md> [--task <prompt>]

    Runs the predict step + a representative invocation under strace+tcpdump
    instrumentation. Requires the parent agentic-skill-behavioral-audit harness scripts to
    be on PATH or accessible relative to this package.
    """
    skill_md_path = Path(args.skill_md)
    if not skill_md_path.exists():
        print(f"error: SKILL.md not found: {skill_md_path}", file=sys.stderr)
        return 1

    # Step 1: predict
    print("[skill-auditor] step 1/2 — predicting capability set from SKILL.md...")
    rc = cmd_predict(args)
    if rc != 0:
        return rc

    # Step 2: run the agent under instrumentation. The full instrumentation
    # pipeline lives in agentic-skill-behavioral-audit/harness/run-skill.sh and depends on
    # strace + tcpdump. We delegate to that script if it's available.
    print("[skill-auditor] step 2/2 — running representative invocation under strace+tcpdump...")
    harness_root_env = subprocess.run(["which", "run-skill.sh"], capture_output=True, text=True)
    if harness_root_env.returncode != 0 or not harness_root_env.stdout.strip():
        print("error: run-skill.sh not found on PATH.", file=sys.stderr)
        print("Either install the parent agentic-skill-behavioral-audit harness, OR pass --harness-dir <path>.", file=sys.stderr)
        return 3

    harness_path = harness_root_env.stdout.strip()
    skill_id = args.skill_id or skill_md_path.parent.name
    rc = subprocess.run([harness_path, skill_id]).returncode
    if rc != 0:
        print(f"error: harness run-skill.sh exited {rc}", file=sys.stderr)
        return rc

    print("[skill-auditor] audit complete; trace.json written alongside SKILL.md")
    return 0


def cmd_policy(args: argparse.Namespace) -> int:
    """skill-auditor policy <SKILL.md> [--out skill-policy.json]

    Generates a deployable skill-policy.json companion artefact from the
    SKILL.md-derived prediction (and optionally the trace, if available).
    """
    skill_md_path = Path(args.skill_md)
    skill_dir = skill_md_path.parent
    skill_id = args.skill_id or skill_dir.name

    pred_path = skill_dir / "prediction.json"
    if not pred_path.exists():
        print(f"error: prediction.json not found at {pred_path}", file=sys.stderr)
        print(f"run `skill-auditor predict {skill_md_path}` first.", file=sys.stderr)
        return 1

    trace_path = skill_dir / "trace.json"
    bundle = build_policy_bundle(skill_id=skill_id,
                                  prediction_path=pred_path,
                                  trace_path=trace_path if trace_path.exists() else None)

    out_path = Path(args.out) if args.out else skill_dir / "skill-policy.json"
    out_path.write_text(json.dumps(bundle, indent=2))
    print(f"wrote {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="skill-auditor",
        description="Behavioural audit toolkit for agentic skills (Putra-Rayhan, 2026)."
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # predict
    sp = sub.add_parser("predict", help="emit prediction.json from SKILL.md text alone")
    sp.add_argument("skill_md", help="path to SKILL.md")
    sp.add_argument("--skill-id", help="skill ID (defaults to parent dir name)")
    sp.add_argument("--effort", default="xhigh", choices=["low", "medium", "high", "xhigh", "max"])
    sp.add_argument("--agent", default="claude", choices=["claude", "codex"])
    sp.add_argument("--timeout", type=int, default=300)
    sp.add_argument("--out", help="output path (default: alongside SKILL.md)")
    sp.set_defaults(func=cmd_predict)

    # audit
    sa = sub.add_parser("audit", help="full audit: predict + instrumented run")
    sa.add_argument("skill_md", help="path to SKILL.md")
    sa.add_argument("--skill-id", help="skill ID (defaults to parent dir name)")
    sa.add_argument("--task", help="task prompt (defaults to reading task.md alongside SKILL.md)")
    sa.add_argument("--effort", default="xhigh", choices=["low", "medium", "high", "xhigh", "max"])
    sa.add_argument("--agent", default="claude", choices=["claude", "codex"])
    sa.add_argument("--timeout", type=int, default=300)
    sa.add_argument("--out", help="output path for prediction.json")
    sa.set_defaults(func=cmd_audit)

    # policy
    sp2 = sub.add_parser("policy", help="emit skill-policy.json companion artefact")
    sp2.add_argument("skill_md", help="path to SKILL.md")
    sp2.add_argument("--skill-id", help="skill ID (defaults to parent dir name)")
    sp2.add_argument("--out", help="output path (default: alongside SKILL.md)")
    sp2.set_defaults(func=cmd_policy)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
