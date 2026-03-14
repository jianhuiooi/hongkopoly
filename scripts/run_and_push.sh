#!/bin/bash
# run_and_push.sh
# ───────────────────────────────────────────────────────────────────────────
# Runs the Hongkopoly simulation AND pushes game_state.json to GitHub
# every N seconds so Netlify serves the live updates.
#
# Usage:
#   bash scripts/run_and_push.sh [--delay 1.0] [--push-every 5]
#
# Requirements:
#   - git remote already set up (git remote add origin <your-repo>)
#   - You're authenticated with GitHub (SSH key or HTTPS token)
# ───────────────────────────────────────────────────────────────────────────

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

DELAY=1.0        # seconds between simulation turns
PUSH_EVERY=5     # push to GitHub every N seconds

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --delay)      DELAY="$2"; shift 2 ;;
    --push-every) PUSH_EVERY="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "▶ Starting simulation (delay=${DELAY}s, push every ${PUSH_EVERY}s)…"

# Run simulation in the background
python "$SCRIPT_DIR/export_state.py" --delay "$DELAY" &
SIM_PID=$!

echo "  Simulation PID: $SIM_PID"
echo "  Pushing public/game_state.json to GitHub every ${PUSH_EVERY}s…"
echo "  Press Ctrl+C to stop."

# Push loop
cd "$ROOT"
while kill -0 "$SIM_PID" 2>/dev/null; do
  sleep "$PUSH_EVERY"
  if kill -0 "$SIM_PID" 2>/dev/null; then
    git add public/game_state.json
    if ! git diff --cached --quiet; then
      git commit -m "🎲 live state update"
      git push origin HEAD 2>&1 | tail -1
    fi
  fi
done

# Final push after sim ends
git add public/game_state.json
git commit -m "🏆 game over — final state" || true
git push origin HEAD || true

echo "✅ Simulation finished. Final state pushed."
