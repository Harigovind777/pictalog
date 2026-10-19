#!/usr/bin/env bash
# Start everything for local use: Ollama (with image support), the server, the web app and the image helper.
# Ctrl-C stops them all.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data

OLLAMA_PORT="${PICTALOG_OLLAMA_PORT:-11435}"
# Ollama 0.32.5 is the last release that makes images (scripts/install-ollama.sh); newer ones only read and write text.
OLLAMA_BIN="${PICTALOG_OLLAMA_BIN:-$HOME/.local/share/pictalog/ollama-0.32.5/ollama}"
if [ ! -x "$OLLAMA_BIN" ]; then
  echo "Ollama 0.32.5 isn't installed, so product photos won't work. Run scripts/install-ollama.sh first." >&2
  OLLAMA_BIN=ollama
fi
if ! curl -sf "http://127.0.0.1:$OLLAMA_PORT/api/version" >/dev/null; then
  OLLAMA_HOST="127.0.0.1:$OLLAMA_PORT" "$OLLAMA_BIN" serve >data/ollama.log 2>&1 &
fi

trap 'kill 0' EXIT INT TERM
uv run uvicorn pictalog.main:create_app --factory --host 0.0.0.0 --port 8000 --reload --reload-dir pictalog --no-access-log &
npm --prefix web run dev -- --port 5173 &
until curl -s -o /dev/null http://127.0.0.1:8000/docs; do sleep 1; done  # wait for the server
PICTALOG_HELPER_OLLAMA_URL="http://127.0.0.1:$OLLAMA_PORT" uv run python -m pictalog_helper &

echo
echo "  Pictalog is running:  http://localhost:5173"
echo
wait
