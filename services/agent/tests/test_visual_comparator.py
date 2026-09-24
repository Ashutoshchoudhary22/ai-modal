"""Visual comparison tests."""

import io
from pathlib import Path

from agent.visual.comparator import VisualComparator
from PIL import Image

FIXTURES = Path(__file__).parent / "fixtures" / "screenshots"


def _png(color: str, size: tuple[int, int] = (100, 80)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_identical_images_pass():
    ref = (FIXTURES / "simple-card" / "reference.png").read_bytes()
    result = VisualComparator(threshold=0.85).compare(ref, ref)
    assert result.passed
    assert result.score >= 0.99


def test_different_images_fail():
    ref = _png("#2563eb")
    gen = _png("#ff0000")
    result = VisualComparator(threshold=0.85).compare(ref, gen)
    assert not result.passed
    assert result.differences


def test_threshold_behavior():
    ref = _png("#2563eb")
    gen = _png("#2570ec")  # slightly different
    strict = VisualComparator(threshold=0.99).compare(ref, gen)
    lenient = VisualComparator(threshold=0.5).compare(ref, gen)
    assert lenient.score >= strict.score


def test_deterministic_output():
    ref = (FIXTURES / "simple-card" / "reference.png").read_bytes()
    c = VisualComparator()
    r1 = c.compare(ref, ref)
    r2 = c.compare(ref, ref)
    assert r1.score == r2.score
    assert r1.passed == r2.passed
