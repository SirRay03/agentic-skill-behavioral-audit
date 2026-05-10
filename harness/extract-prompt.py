#!/usr/bin/env python3
"""Extract the prompt string from a skills/<id>/task.md file's `## Prompt` section.

The prompt is wrapped in a triple- or quadruple-backtick code block. We strip the fence
and return the inner content verbatim (no leading/trailing whitespace).

Usage:
    extract-prompt.py path/to/task.md
"""
import sys
import re
import pathlib


def extract_prompt(task_md_path: pathlib.Path) -> str:
    text = task_md_path.read_text(encoding="utf-8")
    # Match ## Prompt followed by a code fence (3 or 4 backticks), then content, then closing fence
    pattern = re.compile(
        r"##\s+Prompt\s*\n+(`{3,4})\s*\n(.*?)\n\1\s*",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"No `## Prompt` code block found in {task_md_path}")
    return match.group(2).strip()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: extract-prompt.py <task.md>", file=sys.stderr)
        sys.exit(1)
    print(extract_prompt(pathlib.Path(sys.argv[1])))
