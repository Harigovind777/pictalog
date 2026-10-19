---
title: I asked for a size M T-shirt. The AI printed an M on it.
subtitle: Five prompt-engineering lessons from making product photos with a local image model
tags: ai, generative-ai, python, llm, machine-learning
images:
  - spike/out/compare-seed.png  # the three red shirts
---

I'm building **Pictalog**, an app that turns a shop's product list (a spreadsheet, a PDF, or a photo of a printed
price list) into a clean catalog with a photo for every product, and for every size and colour of it. The photos are
made on my laptop by an open image model, FLUX.2 Klein 4B, running in Ollama.

The first real test was the simplest product I could think of: a red cotton T-shirt, size M.

![Three AI-generated red T-shirts. The first two have a small "M" printed on the chest; the third doesn't.](spike/out/compare-seed.png)

Two of the three shirts came back with an **M printed on the chest**. The model had been told "size M" and did the
most literal thing with it.

That one shirt taught me most of what I now know about prompting image models. Here's what changed in the code
because of it.

## 1. An image model draws every word you give it

A language model reads "size M" as a fact about the product. An image model reads it as something to *draw*. So the
prompt should only describe what the camera can see.

Sizes turned out to fall into two kinds:

- **Sizes that change how the product looks**: `1 L`, `350 ml`, `5 kg`. A 1-litre bottle is bigger than a 500 ml one,
  so these stay in the prompt.
- **Sizes that don't**: `M`, `XL`, `8`, `साइज़ 8`. A size M shirt looks exactly like a size L shirt in a studio photo, so
  these are left out.

The rule in code is short: keep a size only if it has a number *and* a unit, and isn't just the word "size"
followed by a number in any of India's languages.

```python
def _visible_size(size: str | None) -> str | None:
    """Sizes with a unit (1 L, 350 ml, 5kg, 1 लीटर) change how a product looks. Letter or bare-number sizes
    (M, XL, 8, साइज़ 8) don't, and putting them in the prompt makes the model print them on the product."""
    if (
        size
        and re.search(r"\d", size)            # has a number
        and re.search(r"[^\W\d_]", size)      # and a unit
        and not re.fullmatch(rf"(?:{_SIZE_WORDS}) \d+", normalise(size))  # and isn't "size 8"
    ):
        return size.strip()
    return None
```

Every prompt also ends with the same studio description, and its last clause does the rest of the work:

> Single product, centered, isolated on a seamless plain white background, soft even studio lighting, sharp focus,
> high detail, true-to-life colours, photorealistic e-commerce photo, **no added text, letters, numbers or watermark.**

## 2. Image models mostly speak English

Product lists aren't all in English. In India a shop's list is as likely to be in Hindi, Tamil or Bengali, and
imported goods bring French or Italian names with them.

An early test product was a French teapot: *Théière*. The image model drew **a bottle**. It had no idea what the word
meant, so it guessed.

The fix is a small step before every photo. A local text model (Qwen 3.5 4B, also in Ollama) rewrites the product into
one plain-English phrase that starts with what the thing *is*:

```text
Théière in Bleu made of Fonte   →   a blue cast-iron teapot
```

The settings are what make that step reliable:

- **Temperature 0**, so the same product always gets the same description.
- **A 120-token cap**, because small models sometimes keep explaining themselves.
- **Keep only the first sentence** of the answer. Anything after it is the model's own commentary.
- **Never block a photo on it.** If the rewrite fails, the original wording goes through.

## 3. Small models copy your examples word for word

My first rewrite instructions had a helpful example in them, something like *"e.g. black peppercorns in a small
bowl"*.

Then a product list came in with **tea** in it, in a language the model didn't know well. The description it wrote
for the tea was "black peppercorns". It had copied the example sentence as its answer.

A different example sentence did the same thing: "a small round copper water pot" showed up for tea and for products
in two scripts the model couldn't read at all.

What worked instead:

- **No example sentences in the instructions at all.**
- **A small glossary passed as notes**, in the form `word = meaning` (`पीतल = brass`). Notes like these give the model
  facts without handing it a sentence to copy.

On my test set of 64 product descriptions across English and 15 Indian languages, scored by whether the description names the
right thing:

| Setup | Right |
|---|---|
| Older model (`qwen3:4b-instruct`) | 32/64 (50%) |
| Qwen 3.5, instructions with an example | 38/64 (59%) |
| Qwen 3.5, no examples, glossary notes | 45/64 (70%) |

Brass, which the older model had turned into "copper", came out right in every language.

## 4. Use the seed to make variants look like one product

Look at the first two shirts again. They are nearly identical, mistakes included, because they share a **seed**. That
is the one useful thing that photo shows.

Ollama's image API honours the seed, and the same seed gives a near-identical picture. Pictalog uses this on purpose:
every variant of a product (the red, blue and black versions of the same shirt) gets the same seed, so they look
like **one product in three colours**, not three different shirts.

```python
def seed_for(group_key: str, offset: int) -> int:
    """Variants of one product share a seed so they look like the same product; regenerating bumps the offset."""
    return int(hashlib.sha256(group_key.encode()).hexdigest()[:8], 16) + offset
```

When someone asks for a new photo, the offset goes up by one and they get a fresh take.

## 5. Write down what still goes wrong

The model isn't perfect, and I keep a list:

- **Mugs with two handles.**
- **Green cardamom drawn as green beans.** The model has simply never learned what cardamom pods look like.
- **Small printed text gets smudged.**

The next experiment is a check-and-retry loop: a small vision model looks at each photo and asks "is this a mug with
one handle?" If the answer is no, the photo is made again with a different seed. If it still fails, the product is
marked "needs your photo", because no picture is better than a wrong one.

## Takeaways

1. Describe only what the camera can see. Labels, sizes and codes end up *printed on the product*.
2. Translate to plain English before you generate, and lead with what the object *is*.
3. Don't put example answers in prompts for small models; they'll copy them. Use `word = meaning` notes.
4. Fix the seed per product so its variants match.
5. Keep a list of known failures, so you know what to test next time.

---

*This is part 1 of a short series on building Pictalog. Part 2 covers running the whole photo studio on a 16 GB
MacBook (and the Ollama update that broke it). Part 3 covers reading price lists in 15 Indian languages.*
