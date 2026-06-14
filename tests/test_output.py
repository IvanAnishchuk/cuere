"""Tests for the output-format dispatcher (cuere.output)."""

import io
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from cuere import (
    CuereError,
    MissingDependencyError,
    OutputFormat,
    QRMatrix,
    UnknownFormatError,
    render,
    render_bytes,
    render_svg,
    save,
)
from cuere.output import coerce_format

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _open_png(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("L")


# ── render_bytes ─────────────────────────────────────────────────


def test_text_bytes_match_render() -> None:
    assert render_bytes("HELLO", format="text") == (render("HELLO") + "\n").encode("utf-8")


def test_text_default_format_is_text() -> None:
    assert render_bytes("HELLO") == render_bytes("HELLO", format=OutputFormat.TEXT)


def test_text_honors_mode_and_invert() -> None:
    expected = (render("HELLO", mode="block", invert=True) + "\n").encode("utf-8")
    assert render_bytes("HELLO", format="text", mode="block", invert=True) == expected


def test_svg_bytes_match_render_svg() -> None:
    matrix = QRMatrix.encode("HELLO")
    assert render_bytes(matrix, format="svg") == render_svg(matrix).encode("utf-8")


def test_svg_is_well_formed_xml() -> None:
    root = ET.fromstring(render_bytes("HELLO", format="svg").decode("utf-8"))
    assert root.tag.endswith("svg")


def test_png_has_signature_and_scaled_size() -> None:
    png = render_bytes("HELLO", format="png", scale=4)
    assert png.startswith(PNG_SIGNATURE)
    matrix = QRMatrix.encode("HELLO")
    assert _open_png(png).size == (matrix.width * 4, matrix.height * 4)


def test_png_pixels_match_matrix_at_scale_one() -> None:
    # At scale 1 every pixel is exactly one module: dark→0, light→255.
    matrix = QRMatrix.encode("HI")
    image = _open_png(render_bytes(matrix, format="png", scale=1))
    for y, row in enumerate(matrix.modules):
        for x, dark in enumerate(row):
            assert image.getpixel((x, y)) == (0 if dark else 255)


def test_png_invert_flips_the_quiet_zone() -> None:
    matrix = QRMatrix.encode("HELLO", border=4)
    normal = _open_png(render_bytes(matrix, format="png", scale=1))
    inverted = _open_png(render_bytes(matrix, format="png", scale=1, invert=True))
    assert normal.getpixel((0, 0)) == 255  # quiet zone is light
    assert inverted.getpixel((0, 0)) == 0  # …and dark once inverted


def test_scale_multiplies_png_dimensions() -> None:
    small = _open_png(render_bytes("HI", format="png", scale=2))
    big = _open_png(render_bytes("HI", format="png", scale=8))
    assert big.size == (small.size[0] * 4, small.size[1] * 4)


def test_encode_options_are_forwarded() -> None:
    # A different border must reach the encoder and change the rendered bytes.
    assert render_bytes("HELLO", format="svg", border=0) != render_bytes("HELLO", format="svg")


@pytest.mark.parametrize("fmt", ["svg", "png"])
def test_non_positive_scale_is_a_clean_error(fmt: str) -> None:
    # A zero/negative scale would make a blank or negatively-sized image; both
    # image formats reject it with a CuereError, never a bare Pillow ValueError.
    with pytest.raises(CuereError):
        _ = render_bytes("HELLO", format=fmt, scale=0)


# ── coerce_format / unknown formats ──────────────────────────────


def test_coerce_format_accepts_str_and_enum() -> None:
    assert coerce_format("png") is OutputFormat.PNG
    assert coerce_format(OutputFormat.SVG) is OutputFormat.SVG


def test_unknown_format_raises() -> None:
    with pytest.raises(UnknownFormatError):
        _ = render_bytes("HELLO", format="jpeg")


def test_unknown_format_message_lists_known_formats() -> None:
    with pytest.raises(UnknownFormatError) as excinfo:
        _ = coerce_format("jpeg")
    message = str(excinfo.value)
    assert "text" in message
    assert "svg" in message
    assert "png" in message


# ── save ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(("suffix", "fmt"), [(".txt", "text"), (".svg", "svg"), (".png", "png")])
def test_save_infers_format_from_suffix(tmp_path: Path, suffix: str, fmt: str) -> None:
    dest = tmp_path / f"code{suffix}"
    save("HELLO", dest)
    assert dest.read_bytes() == render_bytes("HELLO", format=fmt)


def test_save_accepts_a_str_path(tmp_path: Path) -> None:
    dest = tmp_path / "code.svg"
    save("HELLO", str(dest))
    assert dest.read_bytes() == render_bytes("HELLO", format="svg")


def test_save_explicit_format_overrides_suffix(tmp_path: Path) -> None:
    dest = tmp_path / "code.dat"
    save("HELLO", dest, format="svg")
    assert dest.read_bytes() == render_bytes("HELLO", format="svg")


def test_save_writes_to_a_binary_stream() -> None:
    buffer = io.BytesIO()
    save("HELLO", buffer, format="png")
    assert buffer.getvalue().startswith(PNG_SIGNATURE)


def test_save_stream_without_format_raises() -> None:
    with pytest.raises(UnknownFormatError):
        save("HELLO", io.BytesIO())


def test_save_unknown_suffix_raises(tmp_path: Path) -> None:
    with pytest.raises(UnknownFormatError):
        save("HELLO", tmp_path / "code.jpeg")


def test_save_no_suffix_raises(tmp_path: Path) -> None:
    with pytest.raises(UnknownFormatError):
        save("HELLO", tmp_path / "code")


# ── missing optional dependency ──────────────────────────────────


@pytest.fixture
def pillow_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    # A None entry in sys.modules makes `from PIL import Image` raise ImportError,
    # exactly as if the cuere[image] extra were never installed.
    monkeypatch.setitem(sys.modules, "PIL", None)


@pytest.mark.usefixtures("pillow_absent")
def test_png_without_pillow_raises_missing_dependency() -> None:
    with pytest.raises(MissingDependencyError) as excinfo:
        _ = render_bytes("HELLO", format="png")
    assert "cuere[image]" in str(excinfo.value)


@pytest.mark.usefixtures("pillow_absent")
def test_text_and_svg_work_without_pillow() -> None:
    # Only PNG needs Pillow; the other formats must be unaffected by its absence.
    assert render_bytes("HELLO", format="text")
    assert render_bytes("HELLO", format="svg")


def test_importing_cuere_does_not_import_pillow() -> None:
    # PNG export uses Pillow, but only through a lazy import inside cuere.output,
    # so a bare `import cuere` must not pull the optional dependency in.
    code = "import sys, cuere; sys.exit(1 if 'PIL' in sys.modules else 0)"
    result = subprocess.run([sys.executable, "-c", code], check=False)
    assert result.returncode == 0
