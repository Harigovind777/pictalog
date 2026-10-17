"""Spike: time Ollama image generation and save the result. Throwaway.

usage: python spike/imagegen.py MODEL WIDTH HEIGHT NAME "prompt" [seed] [steps] [port]
"""

import base64
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

STUDIO = (
    "Single product, centered, isolated on a seamless plain white background, soft even studio lighting, "
    "sharp focus, high detail, true-to-life colours, photorealistic e-commerce photo, no watermark."
)


def generate(model: str, width: int, height: int, prompt: str, seed: int | None, steps: int | None, port: int) -> dict:
    body: dict = {"model": model, "prompt": prompt, "stream": False, "width": width, "height": height}
    if seed is not None:
        body["seed"] = seed
    if steps is not None:
        body["steps"] = steps
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=900) as res:
        return json.load(res)


def main() -> None:
    model, width, height, name, prompt = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
    seed = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != "-" else None
    steps = int(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7] != "-" else None
    port = int(sys.argv[8]) if len(sys.argv) > 8 else 11435
    start = time.time()
    result = generate(model, width, height, f"{prompt} {STUDIO}", seed, steps, port)
    seconds = time.time() - start
    if "error" in result:
        print("ERROR", result["error"])
        return
    png = base64.b64decode(result["image"])
    out = Path(__file__).parent / "out" / f"{name}.png"
    out.write_bytes(png)
    load = result.get("load_duration", 0) / 1e9
    print(f"{name}: {seconds:.1f}s total ({load:.1f}s load), sha1 {hashlib.sha1(png).hexdigest()[:10]} -> {out.name}")


if __name__ == "__main__":
    main()
