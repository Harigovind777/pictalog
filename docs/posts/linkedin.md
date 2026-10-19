# LinkedIn posts

Plain text: LinkedIn doesn't render Markdown. Each is under 3,000 characters. Replace {LINK} with the Hashnode article's
address once it's published. Post them a few days apart, in this order.

---

## Post 1 (image: spike/out/compare-seed.png)

I asked an AI for a photo of a red T-shirt, size M.

It printed an M on the shirt.

I'm building Pictalog, an app that turns a shop's product list into a catalog with a photo for every product, size and colour. The photos are made on my laptop by an open image model, FLUX.2 Klein 4B.

That one shirt taught me most of what I know about prompting image models:

1. An image model draws every word you give it. "Size M" isn't a fact to it, it's something to draw. Now sizes that change how a product looks (1 L, 5 kg) stay in the prompt. Sizes that don't (M, XL, 8) are left out.

2. Image models mostly speak English. A French "Théière" came out as a bottle. Now a small local text model rewrites every product into plain English first: "a blue cast-iron teapot".

3. Small models copy your examples. I put "black peppercorns" in the instructions as an example, and the model used it as the description for tea. Removing every example sentence and passing "word = meaning" notes instead took accuracy from 59% to 70% across English and 15 Indian languages.

4. Fix the seed per product. Same seed, near-identical picture, so the red, blue and black versions of a shirt look like one product. That's also why two of my three shirts had the same M.

5. Keep a list of what still fails. Mine: mugs with two handles, and green cardamom drawn as green beans.

Full write-up with the code: {LINK}

#GenerativeAI #AI #Python #BuildInPublic

---

## Post 2 (image: spike/out/compare-steps.png)

Can a whole AI product-photo studio run on a 16 GB MacBook?

Yes. But the real budget isn't 16 GB. macOS gives the GPU about 11.3 GB, and I found out from this error:
"model requires 11.9 GiB but only 11.3 GiB are available"

What I learned building the photo side of Pictalog:

→ FLUX.2 Klein 4B (5.7 GB, Apache 2.0) fits. Z-Image Turbo (13 GB) and Klein 9B (12 GB) don't.

→ Cut steps before resolution. 2 steps at 768 px took 34 s, against 49–68 s at the default. 640 px only got me to 50 s. That's about 30 seconds a photo, or 800 photos overnight.

→ Check what a model tag points to. "qwen3:4b" is a thinking build: 75 seconds to rewrite one product name, even with thinking switched off. The instruct build did it in 1 second.

→ Pin your AI runtime like a library. A routine Homebrew upgrade of Ollama removed image generation, and every photo failed with "image generation models are not currently supported". The older version couldn't run the newer text model. Exactly one version, 0.32.5, did both, so the app now installs that exact build, checks its hash and runs it on its own port.

→ Put a queue between the app and the laptop. When the Mac sleeps, uploads wait. Nothing breaks.

Full write-up: {LINK}

#LocalAI #Ollama #GenerativeAI #MachineLearning

---

## Post 3 (image: samples/languages/tamil-pricelist.jpg)

Reading a Tamil price list from a photo, on a laptop, with a 4B model: 86% of fields right across English and 15 Indian languages, and 94% if you leave out two scripts that no local model can read yet.

Five things I learned getting there:

1. Build the test set first. Same 4 products, 16 languages, 4 formats, 176 scored fields per format. One "helpful" change to the instructions dropped accuracy from 90% to 53%. Without the test set I'd never have known.

2. Indian scripts cost 2–4x the tokens. A 6,000-character Odia chunk came to about 9,700 tokens, well past the 4,096-token window. Chunks for Indian scripts are now 2,000 characters.

3. Spreadsheets don't need AI. A dictionary of column names in every language, plus Indian digits (₹ १,२९९, ৳ ২৫০), took them from not recognised at all to 176/176.

4. Combine tools that fail in opposite ways. Tesseract spells Tamil and Odia words exactly but reads ₹ as 2, 3 or %. Qwen 3.5 reads every price right but garbles those words. Now the model gets Tesseract's words with the numbers blanked out, and reads the numbers from the image. On five languages, photo reading went from 9% to 93%.

5. Fix repeated slips with rules, not prompts. A colour given as the size, a price stuck on the end of the name: a small rule-based tidy step took typed lists from 86% to 95%.

Still unsolved: Santali (Ol Chiki) and Manipuri (Meetei Mayek). No local model I tried reads them from a photo. If you know one, please tell me.

Full write-up: {LINK}

#NLP #IndianLanguages #OCR #AI #LLM
