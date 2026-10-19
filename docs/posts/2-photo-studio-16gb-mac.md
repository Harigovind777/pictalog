---
title: A product-photo studio on a 16 GB MacBook
subtitle: Which local AI models fit, how fast they are, and the Ollama update that quietly broke everything
tags: ai, ollama, macos, generative-ai, python
images:
  - spike/out/compare-steps.png  # three black bottles
---

Pictalog turns a shop's product list into a catalog with a realistic studio photo for every product, size and
colour. A clothing shop with 200 products in 4 colours needs 800 photos. Hosted image APIs charge per image, so I
wanted to know: **can the whole studio run on the laptop I already own?**

The laptop is an M4 MacBook with 16 GB of memory. The short answer is yes, with one image model, one small text
model, and a version of Ollama pinned like any other dependency. Here's how it went.

## The real budget is 11.3 GB, not 16

On Apple Silicon the CPU and GPU share memory, but macOS doesn't give the GPU all of it. One of the bigger models I
tried told me exactly how much it could have:

```text
model requires 11.9 GiB but only 11.3 GiB are available
```

About 75% of 16 GB. Every model choice after that was a packing problem:

| Model | Size | Fits? | Notes |
|---|---|---|---|
| Z-Image Turbo | 13 GB | No | The error above |
| FLUX.2 Klein 9B | 12 GB | No | And its licence is non-commercial |
| **FLUX.2 Klein 4B** | **5.7 GB** | **Yes** | Apache 2.0. Chosen |
| Gemma 4 E4B (text) | 6.6 GB | Not next to FLUX | 5.7 + 6.6 is over budget |
| **Qwen 3.5 4B (text)** | **3.3 GB** | **Yes** | Reads documents, writes photo descriptions |

The image model and the text model take turns for every photo: the text model writes an English description of the
product, then FLUX draws it. So both have to fit in the budget together. That, plus weaker results on my tests, ruled out Gemma.

## How fast is "fast enough"?

Ollama's image API is pleasantly boring. One request, one base64 PNG back:

```python
res = httpx.post("http://127.0.0.1:11435/api/generate", json={
    "model": "x/flux2-klein:4b",
    "prompt": prompt,
    "width": 768, "height": 768,
    "seed": seed,     # honoured: same seed, near-identical picture
    "steps": 2,       # honoured too
    "stream": False,
}, timeout=300)
png = base64.b64decode(res.json()["image"])
```

Here's the same bottle at three settings:

![Three AI-generated black water bottles, at 768 px with default steps, 768 px with 2 steps, and 640 px.](spike/out/compare-steps.png)

| Size | Steps | Seconds |
|---|---|---|
| 768 × 768 | default | 49–68 |
| 768 × 768 | **2** | **34** |
| 640 × 640 | default | 50 |

Two steps at 768 px is about twice as fast as the default, and I can't see a difference that matters for a catalog
thumbnail. Making the image smaller saved far less time than cutting steps. **Chosen: 768 px, 2 steps, about 30 seconds
a photo.** That's 800 photos overnight.

## The "thinking" model that wouldn't stop thinking

For the text side I started with `qwen3:4b`. Rewriting one product name into a photo description took **75 seconds**.

The tag `qwen3:4b` is the *thinking* build. Even with `think: false` it still wrote around 400 tokens of reasoning
before answering. The instruct build, `qwen3:4b-instruct`, did the same job in **about 1 second**.

Lesson: on a local model, check which build a tag actually points to. A 75× difference hid in the tag name.

(I later moved reading to Qwen 3.5 4B for its Indian-language accuracy. That's part 3.)

## The update that quietly broke everything

Everything worked. Then I upgraded Ollama through Homebrew to get the newer text models, and every photo failed
with:

```text
image generation models are not currently supported
```

Newer Ollama releases had **removed image generation**. It was there up to 0.32.5. Meanwhile, the older 0.18.2 I'd
started with couldn't download Qwen 3.5 at all ("requires a newer version").

| Ollama | Makes images | Runs Qwen 3.5 |
|---|---|---|
| 0.18.2 | Yes (needs `OLLAMA_LIBRARY_PATH`) | No |
| **0.32.5** | **Yes** | **Yes** |
| 0.40.x | No | Yes |

Only one version did both. So Pictalog now treats Ollama like a pinned dependency:

- An install script downloads the official **0.32.5** build into `~/.local/share/pictalog/`, outside Homebrew, and
  checks its SHA-256.
- The dev script runs that binary on its own port (11435), so the Homebrew or desktop-app copy can keep
  auto-updating without touching it.

If your app depends on a local AI runtime, **pin it like a library**. "Brew upgrade" is not a safe operation for
something your product depends on.

## Fitting it into an app

The Mac isn't a server, so it doesn't act like one:

- The **server** accepts uploads, builds catalogs, and keeps a **queue** of photo jobs.
- The **image helper** on the Mac pulls jobs from the queue, makes the photos, and sends them back.
- When the Mac is asleep, uploads simply wait. The catalog fills in when it wakes up.

That split also means the expensive part could move later, to a rented GPU or a hosted API, without changing the
app.

## What it costs

On the Mac, a photo costs some electricity. Third-party price lists from August–September 2026 put hosted image
generation at roughly **$0.003 to $0.20 per image**, depending on the model. At $0.03, that 800-photo clothing shop is
about $24 per catalog, before any regenerations. For a free tier for small shops, local wins.

## Takeaways

1. On a 16 GB Apple Silicon Mac, plan for **about 11 GB** of GPU memory, shared by every model you load.
2. Cut **steps** before you cut **resolution**.
3. Check whether a model tag is a "thinking" build. It can be 75× slower for the same answer.
4. **Pin your local AI runtime.** A routine upgrade removed the feature my app was built on.
5. Put a queue between the app and the Mac, so a sleeping laptop is a delay, not an outage.

---

*Part 2 of a series on building Pictalog. Part 1: "I asked for a size M T-shirt. The AI printed an M on it." Part 3:
reading price lists in 15 Indian languages with a 4B model.*
