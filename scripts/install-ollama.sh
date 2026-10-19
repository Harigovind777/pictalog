#!/usr/bin/env bash
# Install the Ollama that Pictalog runs and download its models.
#
# Ollama 0.32.5 is the last release that still makes images (later ones answer "image generation models are not
# currently supported"; it is due back on Ollama's new MLX runner). It sits beside any other Ollama, so Homebrew or the
# Ollama app updating themselves can't break product photos.
set -euo pipefail

VERSION=0.32.5
SHA256=5789dd037a86adb328c72c11fc45e6c558452d07e5b50814a8bdb7b0fbdbcd81  # ollama-darwin.tgz, from the release
DIR="$HOME/.local/share/pictalog/ollama-$VERSION"
URL="https://github.com/ollama/ollama/releases/download/v$VERSION/ollama-darwin.tgz"
PORT="${PICTALOG_OLLAMA_PORT:-11435}"
MODELS=(
  x/flux2-klein:4b  # product photos
  qwen3.5:4b        # reading lists, photos and scans in India's languages; English descriptions for photos
)

if [ -x "$DIR/ollama" ]; then
  echo "Ollama $VERSION is already installed in $DIR"
else
  mkdir -p "$DIR"
  curl -fL --progress-bar -o "$DIR/ollama-darwin.tgz" "$URL"
  echo "$SHA256  $DIR/ollama-darwin.tgz" | shasum -a 256 -c -
  tar -xzf "$DIR/ollama-darwin.tgz" -C "$DIR"
  rm "$DIR/ollama-darwin.tgz"
  echo "Installed Ollama $VERSION in $DIR"
fi

export OLLAMA_HOST="127.0.0.1:$PORT"
if ! curl -sf "http://$OLLAMA_HOST/api/version" >/dev/null; then
  "$DIR/ollama" serve >/dev/null 2>&1 &
  trap 'kill $!' EXIT
  until curl -sf "http://$OLLAMA_HOST/api/version" >/dev/null; do sleep 1; done
fi
for model in "${MODELS[@]}"; do
  "$DIR/ollama" pull "$model"
done
