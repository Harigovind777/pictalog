import io

import pytest
from PIL import Image

from pictalog.images import new_image_keys, to_webp_pair


def png_bytes(width: int, height: int, color=(200, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, "PNG")
    return buf.getvalue()


def test_to_webp_pair():
    full, thumb = to_webp_pair(png_bytes(1000, 500))
    assert Image.open(io.BytesIO(full)).format == "WEBP"
    assert Image.open(io.BytesIO(full)).size == (1000, 500)
    assert Image.open(io.BytesIO(thumb)).size == (400, 200)


def test_to_webp_pair_rejects_non_image():
    with pytest.raises(ValueError):
        to_webp_pair(b"nope")


def test_new_image_keys():
    full, thumb = new_image_keys()
    assert full.startswith("img/") and full.endswith(".webp")
    assert thumb == full.removesuffix(".webp") + "_t.webp"
