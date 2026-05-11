#!/usr/bin/env bash
# Cross-agent variant of run-skill.sh — runs the same task.md prompt under
# OpenAI's Codex CLI instead of Claude Code, captures the same strace + tcpdump
# instrumentation, and writes to skills/<id>/trace-codex.json.
#
# Usage:  run-skill-codex.sh <skill-id>
# Run from inside a Linux environment with strace + tcpdump (project root inferred from script location).
set -euo pipefail

SKILL_ID="${1:?usage: run-skill-codex.sh <skill-id>}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
HARNESS="$PROJECT_ROOT/harness"

# Same PATH as run-skill.sh + codex via npm global
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
SKILL_DIR="$PROJECT_ROOT/skills/$SKILL_ID"
RAW_DIR="$SKILL_DIR/raw-codex"
WORK_DIR="/tmp/work-codex-$SKILL_ID"

if [ ! -d "$SKILL_DIR" ]; then
  echo "ERROR: skill dir not found: $SKILL_DIR" >&2
  exit 1
fi
if [ ! -f "$SKILL_DIR/task.md" ]; then
  echo "ERROR: task.md not found: $SKILL_DIR/task.md" >&2
  exit 1
fi

# Prepare clean dirs
rm -rf "$RAW_DIR" "$WORK_DIR"
mkdir -p "$RAW_DIR" "$WORK_DIR"

# Pre-seed workspace fixture if available
if [ -d "$HARNESS/workspaces/$SKILL_ID" ]; then
  cp -r "$HARNESS/workspaces/$SKILL_ID/." "$WORK_DIR/"
  echo "[seed] copied fixture from $HARNESS/workspaces/$SKILL_ID/"
fi

# Build a Codex-compatible prompt: Codex doesn't auto-load skills, so we inline
# the SKILL.md content into the prompt. This is methodologically distinct from
# Claude Code (which loads skills automatically) — but the comparison axis is
# what the agent does at runtime given the SAME SKILL.md text + task.
PROMPT_SKILL_MD="$(cat "$SKILL_DIR/SKILL.md")"
PROMPT_TASK="$(python3 "$HARNESS/extract-prompt.py" "$SKILL_DIR/task.md")"
PROMPT_FULL="You have access to the following 'agentic skill'. Read it carefully and follow its instructions to accomplish the task at the bottom.

=== SKILL.md ===
${PROMPT_SKILL_MD}
=== END SKILL.md ===

Task: ${PROMPT_TASK}"

PROMPT_PREVIEW="$(printf '%s' "$PROMPT_FULL" | tail -c 200 | tr '\n' ' ')"

cd "$WORK_DIR"

echo "============================================================"
echo "[run-skill-codex] $SKILL_ID"
echo "[run-skill-codex] workdir: $WORK_DIR"
echo "[run-skill-codex] prompt tail: ...${PROMPT_PREVIEW}"
echo "============================================================"

# Start tcpdump in background.
tcpdump -i any -U -w "$RAW_DIR/net.pcap" \
  '(udp port 53) or (tcp[tcpflags] & tcp-syn != 0)' \
  >"$RAW_DIR/tcpdump.log" 2>&1 &
TCPDUMP_PID=$!
sleep 1

# Run codex under strace, with a 10-minute hard timeout.
# Browser-spawning skills (agent-browser, cookie-sync) leave orphan Chrome
# processes that block strace's wait-for-children. The timeout cuts the wait
# short; cleanup explicitly hunts orphan agent-browser-chrome / chromium /
# firebase-tools processes before parsing the trace.
START_TS=$(date -u +%s)
set +e
timeout --kill-after=30 600 \
  strace -f -e trace=openat,open,creat,write,unlink,unlinkat,rename,renameat,connect -s 256 \
    -o "$RAW_DIR/syscalls.log" \
    codex exec \
      --dangerously-bypass-approvals-and-sandbox \
      -C "$WORK_DIR" \
      "$PROMPT_FULL" \
      </dev/null \
      >"$RAW_DIR/codex-stdout.txt" 2>"$RAW_DIR/codex-stderr.log"
CODEX_EXIT=$?
set -e
END_TS=$(date -u +%s)

# Cleanup orphan browser-spawning skill processes that hold strace open.
pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
pkill -KILL -f "firebase-tools" 2>/dev/null || true
pkill -KILL -f "puppeteer" 2>/dev/null || true

# Stop tcpdump cleanly
sleep 1
kill -INT "$TCPDUMP_PID" 2>/dev/null || true
wait "$TCPDUMP_PID" 2>/dev/null || true

DURATION=$((END_TS - START_TS))
echo "[run-skill-codex] codex exit=$CODEX_EXIT, duration=${DURATION}s"
echo "[run-skill-codex] syscalls: $(wc -l < "$RAW_DIR/syscalls.log") lines"
echo "[run-skill-codex] pcap: $(stat -c%s "$RAW_DIR/net.pcap" 2>/dev/null || echo 0) bytes"

# Parse traces
python3 "$HARNESS/parse-strace.py" "$RAW_DIR/syscalls.log" > "$RAW_DIR/fs-trace.json"
python3 "$HARNESS/parse-pcap.py" "$RAW_DIR/net.pcap" > "$RAW_DIR/net-trace.json"

# Combine
python3 <<EOF
import json, pathlib
fs = json.loads(pathlib.Path("$RAW_DIR/fs-trace.json").read_text())
net = json.loads(pathlib.Path("$RAW_DIR/net-trace.json").read_text())
trace = {
  "skill_id": "$SKILL_ID",
  "agent": "codex",
  "codex_exit": $CODEX_EXIT,
  "duration_seconds": $DURATION,
  "fs": fs,
  "net": net,
}
pathlib.Path("$SKILL_DIR/trace-codex.json").write_text(json.dumps(trace, indent=2))
print(f"[run-skill-codex] wrote $SKILL_DIR/trace-codex.json")
EOF

echo "============================================================"
echo "[run-skill-codex] DONE: $SKILL_ID"
echo "============================================================"
