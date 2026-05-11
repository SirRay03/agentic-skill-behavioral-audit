#!/usr/bin/env bash
# Effort-parametric variant of run-skill.sh — accepts EFFORT_OVERRIDE env var
# (default / high / xhigh / max). Used by Phase 3.N runtime effort sensitivity.
set -euo pipefail

SKILL_ID="${1:?usage: run-skill-effort.sh <skill-id>}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
HARNESS="$PROJECT_ROOT/harness"
EFFORT="${EFFORT_OVERRIDE:-high}"

export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
[ -f "$HOME/.skill-audit-creds" ] && source "$HOME/.skill-audit-creds"

TRACE_SUFFIX="${TRACE_SUFFIX:-}"
SKILL_DIR="$PROJECT_ROOT/skills/$SKILL_ID"
RAW_DIR="$SKILL_DIR/raw${TRACE_SUFFIX}"
WORK_DIR="/tmp/work${TRACE_SUFFIX}-$SKILL_ID"
TRACE_FILE="$SKILL_DIR/trace${TRACE_SUFFIX}.json"

if [ ! -d "$SKILL_DIR" ] || [ ! -f "$SKILL_DIR/task.md" ]; then
  echo "ERROR: skill dir or task.md missing for $SKILL_ID" >&2; exit 1
fi

rm -rf "$RAW_DIR" "$WORK_DIR"
mkdir -p "$RAW_DIR" "$WORK_DIR"

if [ -d "$HARNESS/workspaces/$SKILL_ID" ]; then
  cp -r "$HARNESS/workspaces/$SKILL_ID/." "$WORK_DIR/"
fi

PROMPT="$(python3 "$HARNESS/extract-prompt.py" "$SKILL_DIR/task.md")"
cd "$WORK_DIR"

echo "============================================================"
echo "[run-skill-effort] $SKILL_ID effort=$EFFORT"
echo "============================================================"

tcpdump -i any -U -w "$RAW_DIR/net.pcap" \
  '(udp port 53) or (tcp[tcpflags] & tcp-syn != 0)' \
  >"$RAW_DIR/tcpdump.log" 2>&1 &
TCPDUMP_PID=$!
sleep 1

START_TS=$(date -u +%s)
set +e
timeout --kill-after=30 900 \
  strace -f -e trace=openat,open,creat,write,unlink,unlinkat,rename,renameat,connect -s 256 \
    -o "$RAW_DIR/syscalls.log" \
    claude -p "$PROMPT" \
      --dangerously-skip-permissions \
      --output-format json \
      --no-session-persistence \
      --effort "$EFFORT" \
      </dev/null \
      >"$RAW_DIR/claude-stdout.json" 2>"$RAW_DIR/claude-stderr.log"
CLAUDE_EXIT=$?
set -e
END_TS=$(date -u +%s)

pkill -KILL -f "agent-browser-chrome-" 2>/dev/null || true
pkill -KILL -f "firebase-tools" 2>/dev/null || true
sleep 1
kill -INT "$TCPDUMP_PID" 2>/dev/null || true
wait "$TCPDUMP_PID" 2>/dev/null || true

DURATION=$((END_TS - START_TS))
echo "[run-skill-effort] claude exit=$CLAUDE_EXIT, duration=${DURATION}s, effort=$EFFORT"
echo "[run-skill-effort] syscalls: $(wc -l < "$RAW_DIR/syscalls.log") lines"
echo "[run-skill-effort] pcap: $(stat -c%s "$RAW_DIR/net.pcap" 2>/dev/null || echo 0) bytes"

python3 "$HARNESS/parse-strace.py" "$RAW_DIR/syscalls.log" > "$RAW_DIR/fs-trace.json"
python3 "$HARNESS/parse-pcap.py" "$RAW_DIR/net.pcap" > "$RAW_DIR/net-trace.json"

python3 <<EOF
import json, pathlib
fs = json.loads(pathlib.Path("$RAW_DIR/fs-trace.json").read_text())
net = json.loads(pathlib.Path("$RAW_DIR/net-trace.json").read_text())
trace = {
  "skill_id": "$SKILL_ID",
  "effort": "$EFFORT",
  "claude_exit": $CLAUDE_EXIT,
  "duration_seconds": $DURATION,
  "fs": fs,
  "net": net,
}
pathlib.Path("$TRACE_FILE").write_text(json.dumps(trace, indent=2))
print(f"[run-skill-effort] wrote $TRACE_FILE")
EOF
