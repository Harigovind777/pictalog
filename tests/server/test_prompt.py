from pictalog.catalog.prompt import STUDIO, build_prompt, seed_for
from pictalog.models import Product, Variant


def test_build_prompt_full():
    product = Product(name="Classic Tee", brand="Acme", category="Apparel", description="Soft cotton crew neck")
    variant = Variant(colour="Red", material="Cotton", size="M")
    assert build_prompt(product, variant) == (
        "Professional studio product photograph of Classic Tee by Acme in Red made of Cotton, size M (Apparel). "
        "Soft cotton crew neck. " + STUDIO
    )


def test_build_prompt_name_only():
    assert build_prompt(Product(name="Mug"), Variant()) == "Professional studio product photograph of Mug. " + STUDIO


def test_build_prompt_description_only_is_the_subject():
    prompt = build_prompt(Product(description="Blue ceramic mug"), Variant())
    assert prompt == "Professional studio product photograph of Blue ceramic mug. " + STUDIO


def test_build_prompt_truncates_description():
    prompt = build_prompt(Product(name="Mug", description="x" * 500), Variant())
    assert "x" * 300 in prompt and "x" * 301 not in prompt


def test_studio_wording():
    assert STUDIO == (
        "Single product, centered, isolated on a seamless plain white background, soft even studio lighting, "
        "sharp focus, high detail, true-to-life colours, photorealistic e-commerce photo, no watermark."
    )


def test_seed_shared_by_variants():
    assert seed_for("acme|tee", 0) == seed_for("acme|tee", 0)
    assert seed_for("acme|tee", 1) == seed_for("acme|tee", 0) + 1
    assert seed_for("acme|tee", 0) != seed_for("acme|mug", 0)
