import pytest

from pictalog_helper.config import HelperSettings


@pytest.fixture
def settings():
    # The OCR-then-text path; tests of vision and Tesseract switch them on.
    return HelperSettings(
        image_model="x/flux2-klein:4b", width=768, height=768, steps=2, text_model="qwen3.5:4b", vision=False,
        tesseract=False, ocr_model="glm-ocr",
    )
