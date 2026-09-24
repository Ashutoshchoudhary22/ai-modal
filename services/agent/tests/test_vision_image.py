"""Image validation tests."""

import io
from pathlib import Path

import pytest
from agent.vision.errors import VisionError
from agent.vision.image import ImageValidator
from ai_platform_protocol.vision import ImageInput, VisionErrorCode
from PIL import Image

FIXTURES = Path(__file__).parent / "fixtures" / "screenshots"


@pytest.fixture
def validator() -> ImageValidator:
    return ImageValidator(
        max_bytes=1_000_000, max_width=1024, max_height=1024, max_pixels=1_048_576
    )


def _png_bytes(width: int = 100, height: int = 80, color: str = "#2563eb") -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_valid_png(validator: ImageValidator):
    meta = validator.validate(ImageInput(data=_png_bytes(), mime_type="image/png"))
    assert meta.mime_type == "image/png"
    assert meta.width == 100
    assert meta.height == 80


def test_valid_jpeg(validator: ImageValidator):
    img = Image.new("RGB", (50, 50), "#ff0000")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    meta = validator.validate(ImageInput(data=buf.getvalue(), mime_type="image/jpeg"))
    assert meta.mime_type == "image/jpeg"


def test_valid_webp(validator: ImageValidator):
    img = Image.new("RGB", (50, 50), "#00ff00")
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    meta = validator.validate(ImageInput(data=buf.getvalue(), mime_type="image/webp"))
    assert meta.mime_type == "image/webp"


def test_invalid_mime(validator: ImageValidator):
    with pytest.raises(VisionError) as exc:
        validator.validate(ImageInput(data=b"data", mime_type="image/gif"))
    assert exc.value.code == VisionErrorCode.UNSUPPORTED_IMAGE_FORMAT


def test_corrupted_image(validator: ImageValidator):
    with pytest.raises(VisionError) as exc:
        validator.validate(ImageInput(data=b"not-an-image", mime_type="image/png"))
    assert exc.value.code == VisionErrorCode.INVALID_IMAGE


def test_oversized_image(validator: ImageValidator):
    with pytest.raises(VisionError) as exc:
        validator.validate(ImageInput(data=_png_bytes(2000, 2000), mime_type="image/png"))
    assert exc.value.code == VisionErrorCode.IMAGE_DIMENSIONS_EXCEEDED


def test_oversized_bytes(validator: ImageValidator):
    with pytest.raises(VisionError) as exc:
        validator.validate(ImageInput(data=b"x" * 2_000_000, mime_type="image/png"))
    assert exc.value.code in {
        VisionErrorCode.IMAGE_TOO_LARGE,
        VisionErrorCode.INVALID_IMAGE,
    }


def test_fixture_png(validator: ImageValidator):
    data = (FIXTURES / "simple-card" / "reference.png").read_bytes()
    meta = validator.validate(
        ImageInput(data=data, mime_type="image/png", filename="reference.png")
    )
    assert meta.width == 200
