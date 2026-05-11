#!/usr/bin/env bash
# Run one skill end-to-end: prep workspace, start tcpdump, run claude under strace,
# parse traces, write skills/<id>/trace.json
#
# Usage:  run-skill.sh <skill-id>
# Run from inside a Linux environment with strace + tcpdump (project root inferred from script location).
set -euo pipefail

SKILL_ID="${1:?usage: run-skill.sh <skill-id>}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
HARNESS="$PROJECT_ROOT/harness"

# Ensure per-skill CLIs are on PATH (npm-global + pip user-installs)
# regardless of whether this script is invoked from a login shell.
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

# Source real credentials if available (for the realcreds variant runs).
# File is gitignored; per-skill harness inherits these env vars.
if [ -f "$HOME/.skill-audit-creds" ]; then
  # shellcheck source=/dev/null
  source "$HOME/.skill-audit-creds"
fi

# TRACE_SUFFIX env var lets the caller distinguish run variants (e.g.
# TRACE_SUFFIX=-realcreds). Default empty preserves the original layout.
TRACE_SUFFIX="${TRACE_SUFFIX:-}"
SKILL_DIR="$PROJECT_ROOT/skills/$SKILL_ID"
RAW_DIR="$SKILL_DIR/raw${TRACE_SUFFIX}"
WORK_DIR="/tmp/work${TRACE_SUFFIX}-$SKILL_ID"
TRACE_FILE="$SKILL_DIR/trace${TRACE_SUFFIX}.json"

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

# Extract prompt
PROMPT="$(python3 "$HARNESS/extract-prompt.py" "$SKILL_DIR/task.md")"
PROMPT_PREVIEW="$(printf '%s' "$PROMPT" | head -c 100 | tr '\n' ' ')"

cd "$WORK_DIR"

echo "============================================================"
echo "[run-skill] $SKILL_ID"
echo "[run-skill] workdir: $WORK_DIR"
echo "[run-skill] prompt: ${PROMPT_PREVIEW}..."
echo "============================================================"

# Start tcpdump in background. Capture DNS (port 53) and TCP-SYN packets.
# tcpdump exits cleanly via SIGINT (kill -INT) so it flushes the pcap buffer.
tcpdump -i any -U -w "$RAW_DIR/net.pcap" \
  '(udp port 53) or (tcp[tcpflags] & tcp-syn != 0)' \
  >"$RAW_DIR/tcpdump.log" 2>&1 &
TCPDUMP_PID=$!
sleep 1  # let tcpdump bind

# Run claude under strace. claude reads from stdin if -p given a prompt arg, but
# we explicitly close stdin so it doesn't hang waiting for input.
# 15-min hard timeout protects against the refusal-loop pattern observed on
# adversarial mutation skills (Phase 1.C). Default `claude -p` has no
# self-imposed timeout, so we wrap it in `timeout`.
START_TS=$(date -u +%s)
set +e
timeout --kill-after=30 900 \
  strace -f -e trace=openat,open,creat,write,unlink,unlinkat,rename,renameat,connect -s 256 \
    -o "$RAW_DIR/syscalls.log" \
    claude -p "$PROMPT" \
      --dangerously-skip-permissions \
      --output-format json \
      --no-session-persistence \
      --effort high \
      </dev/null \
      >"$RAW_DIR/claude-stdout.json" 2>"$RAW_DIR/claude-stderr.log"
CLAUDE_EXIT=$?
set -e
END_TS=$(date -u +%s)

# Stop tcpdump cleanly so it flushes the buffer
sleep 1
kill -INT "$TCPDUMP_PID" 2>/dev/null || true
wait "$TCPDUMP_PID" 2>/dev/null || true

DURATION=$((END_TS - START_TS))
echo "[run-skill] claude exit=$CLAUDE_EXIT, duration=${DURATION}s"
echo "[run-skill] syscalls: $(wc -l < "$RAW_DIR/syscalls.log") lines"
echo "[run-skill] pcap: $(stat -c%s "$RAW_DIR/net.pcap" 2>/dev/null || echo 0) bytes"

# Parse traces
python3 "$HARNESS/parse-strace.py" "$RAW_DIR/syscalls.log" > "$RAW_DIR/fs-trace.json"
python3 "$HARNESS/parse-pcap.py" "$RAW_DIR/net.pcap" > "$RAW_DIR/net-trace.json"

# Combine into trace.json with metadata
python3 <<EOF
import json, pathlib
fs = json.loads(pathlib.Path("$RAW_DIR/fs-trace.json").read_text())
net = json.loads(pathlib.Path("$RAW_DIR/net-trace.json").read_text())
trace = {
  "skill_id": "$SKILL_ID",
  "claude_exit": $CLAUDE_EXIT,
  "duration_seconds": $DURATION,
  "fs": fs,
  "net": net,
}
pathlib.Path("$TRACE_FILE").write_text(json.dumps(trace, indent=2))
print(f"[run-skill] wrote $TRACE_FILE")
EOF

echo "============================================================"
echo "[run-skill] DONE: $SKILL_ID"
echo "============================================================"
