# Spike notes — local AI on the M4 (16 GB)

## Ollama image generation

- Homebrew's Ollama 0.18.2 needs **`OLLAMA_LIBRARY_PATH=/opt/homebrew/lib`** when started, or image models fail with
  `libmlxc.dylib not found` (the MLX library comes from Homebrew's `mlx-c`).
- Request: `POST /api/generate` with top-level fields
  `{"model", "prompt", "stream": false, "width", "height", "seed", "steps"}`.
- Response: `{"image": "<base64 PNG>", "done": true, "total_duration": ns, "load_duration": ns, ...}`;
  failures come back as `{"error": "..."}`.
- `seed` is honoured: the same seed gives a near-identical picture (tiny GPU differences, not byte-identical).
- `steps` is honoured.

### FLUX.2 Klein 4B (`x/flux2-klein:4b`, 5.7 GB, Apache 2.0)

| size | steps | seconds |
|------|-------|---------|
| 768² | default | 49–68 |
| 768² | 2 | 34 |
| 640² | default | 50 |

Realistic studio product shots (tee, bottle, mug). Failure seen: a mug with two handles.
**"size M" in the prompt printed an M on the shirt** → prompts now leave out letter sizes and ask for no added text.

### Z-Image Turbo (`x/z-image-turbo`, 13 GB)

Pending download.

## Text extraction

Pending: `qwen3:4b` via `/api/chat` with `format` = JSON schema and `think: false`; `glm-ocr` for photos/scans.
