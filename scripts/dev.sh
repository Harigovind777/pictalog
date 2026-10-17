#!/usr/bin/env bash
# Start everything for local use: Ollama (with image support), the server, the web app and the image helper.
# Ctrl-C stops them all.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data

OLLAMA_PORT="${PICTALOG_OLLAMA_PORT:-11435}"
if ! curl -sf "http://127.0.0.1:$OLLAMA_PORT/api/version" >/dev/null; then
  # Homebrew's Ollama only finds its image (MLX) library with this path set.
  OLLAMA_HOST="127.0.0.1:$OLLAMA_PORT" OLLAMA_LIBRARY_PATH=/opt/homebrew/lib ollama serve >data/ollama.log 2>&1 &
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
