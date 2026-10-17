import pytest

from pictalog_helper.config import HelperSettings


@pytest.fixture
def settings():
    return HelperSettings(image_model="x/flux2-klein:4b", width=768, height=768, steps=2, text_model="qwen3:4b")
