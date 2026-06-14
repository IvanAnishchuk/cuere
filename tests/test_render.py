"""Glyph-level and golden-output tests for the renderers."""

from pathlib import Path

import pytest

from cuere import QRMatrix, RenderMode, render, render_height, render_matrix, render_width
from cuere.render import ANSI_PREFIX, ANSI_RESET

GOLDEN = Path(__file__).parent / "golden"
WC_URI = (
    "wc:7f6e504bfad60b485450578e05678ed3e8e8c4751d3c6160be17160d63ec90f9@2"
    "?relay-protocol=irn"
    "&symKey=587d5484ce2a2a6ee3ba1962fdd7e8588e06200c46823bd18fbd67def96ad303"
)


def _matrix(rows: list[list[bool]]) -> QRMatrix:
    return QRMatrix(modules=tuple(tuple(row) for row in rows), version=1, border=0)


# ── glyph mapping ────────────────────────────────────────────────


def test_half_glyphs_even_height() -> None:
    matrix = _matrix([[True, False], [False, True]])
    assert render_matrix(matrix) == "▀▄"


def test_half_glyphs_all_combinations() -> None:
    matrix = _matrix([[False, True, False, True], [False, False, True, True]])
    assert render_matrix(matrix) == " ▀▄█"


def test_half_glyphs_odd_height_pads_light_row() -> None:
    matrix = _matrix([[True, True], [False, True], [True, False]])
    assert render_matrix(matrix) == "▀█\n▀ "


def test_block_mode() -> None:
    matrix = _matrix([[True, False], [False, True]])
    assert render_matrix(matrix, mode=RenderMode.BLOCK) == "██  \n  ██"


def test_ansi_mode_wraps_each_line() -> None:
    matrix = _matrix([[True, False], [False, True]])
    out = render_matrix(matrix, mode=RenderMode.ANSI)
    assert out == f"{ANSI_PREFIX}▀▄{ANSI_RESET}"


def test_invert_equals_rendering_the_inverted_matrix() -> None:
    matrix = QRMatrix.encode("HELLO")
    for mode in RenderMode:
        assert render_matrix(matrix, mode=mode, invert=True) == render_matrix(
            matrix.inverted(), mode=mode
        )


def test_empty_matrix_renders_empty() -> None:
    assert render_matrix(_matrix([])) == ""


def test_empty_payload_renders_a_valid_code() -> None:
    # An empty payload is encodable (version 1), so it must render as a normal
    # rectangular half-block code with dark modules, not an empty string.
    out = render("")
    lines = out.split("\n")
    assert len(lines) == render_height(QRMatrix.encode(""))
    assert len({len(line) for line in lines}) == 1
    assert {"▀", "▄", "█"} & set(out)  # has ink, not just quiet zone


@pytest.mark.parametrize("mode", list(RenderMode))
def test_extreme_border_renders_rectangular_with_blank_frame(mode: RenderMode) -> None:
    # A large quiet zone stays rectangular and the outermost rendered row is
    # pure quiet zone (blank once any SGR wrapper is stripped).
    out = render("HI", mode=mode, border=20)
    lines = out.split("\n")
    assert len({len(line) for line in lines}) == 1
    top = lines[0].replace(ANSI_PREFIX, "").replace(ANSI_RESET, "")
    assert set(top) <= {" "}


# ── dimensions ───────────────────────────────────────────────────


def test_width_and_height_arithmetic() -> None:
    matrix = QRMatrix.encode("HELLO")  # 29x29 with border
    assert render_width(matrix, RenderMode.HALF) == 29
    assert render_width(matrix, RenderMode.ANSI) == 29
    assert render_width(matrix, RenderMode.BLOCK) == 58
    assert render_height(matrix, RenderMode.HALF) == 15  # ceil(29 / 2)
    assert render_height(matrix, RenderMode.ANSI) == 15
    assert render_height(matrix, RenderMode.BLOCK) == 29


@pytest.mark.parametrize("mode", list(RenderMode))
def test_lines_are_equal_width(mode: RenderMode) -> None:
    out = render("HELLO WORLD", mode=mode)
    lines = out.split("\n")
    assert len({len(line) for line in lines}) == 1
    assert len(lines) == render_height(QRMatrix.encode("HELLO WORLD"), mode)


# ── golden outputs (scan these with a phone when they change) ────


@pytest.mark.parametrize("mode", ["half", "block", "ansi"])
def test_golden_hello(mode: str) -> None:
    expected = (GOLDEN / f"hello_{mode}.txt").read_text(encoding="utf-8")
    assert render("HELLO WORLD", mode=mode) + "\n" == expected


def test_golden_walletconnect_uri_fits_80_columns() -> None:
    out = render(WC_URI)
    assert out + "\n" == (GOLDEN / "wc_uri_half.txt").read_text(encoding="utf-8")
    assert all(len(line) <= 80 for line in out.split("\n"))
