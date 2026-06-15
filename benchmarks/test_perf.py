"""Performance benchmarks for cuere's encode and render paths.

Run with ``uv run pytest benchmarks/ --benchmark-only --no-cov``. These are
deliberately kept out of the test suite — ``testpaths = ["tests"]`` in
``pyproject.toml`` means a bare ``uv run pytest`` never collects this directory,
so the 100%-branch-coverage suite is untouched. An informational CI job
(``.github/workflows/benchmark.yml``) runs them and records the timings as a
JSON artifact. See ``benchmarks/README.md``.

The benchmarks are layered so a regression can be attributed:

* ``encode`` group — the segno round-trip in :meth:`QRMatrix.encode` alone.
* ``render`` group — each renderer on a *pre-built* matrix, so encode time is
  excluded and only the glyph/vector/raster cost is measured.
* ``high-level`` group — the user-facing ``render`` / ``render_bytes`` path
  (coerce -> encode -> render) end to end.
"""

import importlib.util

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from cuere import (
    QRMatrix,
    RenderMode,
    render,
    render_bytes,
    render_matrix,
    render_svg,
)

# Representative payloads spanning the QR version range, as fixed literals (no
# randomness) so timings stay comparable run to run. The medium payload is a
# realistic BIP-21 wallet URI and carries no secret-like token, so the gitleaks
# scan (allowlisted only for tests/test_render.py) stays quiet here.
SHORT_PAYLOAD = "https://example.com/qr"
MEDIUM_PAYLOAD = (
    "bitcoin:bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
    "?amount=0.005&label=Coffee&message=Order%201234"
)
LONG_PAYLOAD = "A" * 1000

PAYLOADS = {
    "short": SHORT_PAYLOAD,
    "medium": MEDIUM_PAYLOAD,
    "long": LONG_PAYLOAD,
}

# The large (~1 KB) payload is the meaningful render case (the renderers are
# O(modules)); build its matrix once so the render benchmarks measure only render
# time, not encode time.
LARGE_MATRIX = QRMatrix.encode(LONG_PAYLOAD)

_PILLOW_AVAILABLE = importlib.util.find_spec("PIL") is not None


@pytest.mark.benchmark(group="encode")
@pytest.mark.parametrize("payload", list(PAYLOADS.values()), ids=list(PAYLOADS))
def test_encode(benchmark: BenchmarkFixture, payload: str) -> None:
    """Encode each payload size into a QR matrix (segno round-trip)."""
    matrix = benchmark(QRMatrix.encode, payload)
    assert matrix.width > 0


@pytest.mark.benchmark(group="render")
@pytest.mark.parametrize("mode", list(RenderMode), ids=[mode.value for mode in RenderMode])
def test_render_mode(benchmark: BenchmarkFixture, mode: RenderMode) -> None:
    """Render the large matrix as text in each mode (half / block / ansi)."""
    text = benchmark(render_matrix, LARGE_MATRIX, mode=mode)
    assert text


@pytest.mark.benchmark(group="render")
def test_render_svg(benchmark: BenchmarkFixture) -> None:
    """Render the large matrix as an SVG document."""
    svg = benchmark(render_svg, LARGE_MATRIX)
    assert svg.startswith("<?xml")


@pytest.mark.benchmark(group="render")
@pytest.mark.skipif(not _PILLOW_AVAILABLE, reason="PNG needs the cuere[image] extra (Pillow)")
def test_render_png(benchmark: BenchmarkFixture) -> None:
    """Render the large matrix as PNG bytes (requires Pillow)."""
    png = benchmark(render_bytes, LARGE_MATRIX, format="png")
    assert png.startswith(b"\x89PNG")


@pytest.mark.benchmark(group="high-level")
def test_high_level_render(benchmark: BenchmarkFixture) -> None:
    """The user-facing encode -> render text path on a medium payload."""
    text = benchmark(render, MEDIUM_PAYLOAD)
    assert text


@pytest.mark.benchmark(group="high-level")
def test_high_level_render_bytes_svg(benchmark: BenchmarkFixture) -> None:
    """The user-facing encode -> SVG bytes path on a medium payload."""
    data = benchmark(render_bytes, MEDIUM_PAYLOAD, format="svg")
    assert data
