"""Glyph-level and golden-output tests for the renderers."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from cuere import (
    Color,
    ColorError,
    CuereError,
    QRMatrix,
    RenderMode,
    render,
    render_height,
    render_matrix,
    render_width,
)
from cuere.render import (
    ANSI_BG,
    ANSI_FG,
    ANSI_PREFIX,
    ANSI_RESET,
    DEFAULT_SCALE,
    _resolve_rgb,  # pyright: ignore[reportPrivateUsage]
    check_color_mode,
    render_svg,
    resolve_color,
)

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


# ── colors ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        ("red", 1),
        ("WHITE", 7),
        ("Bright Red", 9),
        ("bright-blue", 12),
        (16, 16),
        ("231", 231),
        ("#ff8800", (255, 136, 0)),
        ("#f80", (255, 136, 0)),
        ((1, 2, 3), (1, 2, 3)),
        ("1,2,3", (1, 2, 3)),
        (" 1 , 2 , 3 ", (1, 2, 3)),
    ],
)
def test_resolve_color_accepts_every_form(
    color: Color, expected: int | tuple[int, int, int]
) -> None:
    assert resolve_color(color) == expected


@pytest.mark.parametrize(
    "color",
    # "²"/"٤" are unicode digits str.isdigit() accepts but int() can't (or
    # silently would) treat as an ASCII palette index — both must be rejected.
    ["bleu", "", "#", "#12", "#1234", "#gg0000", "1,2", "1,2,3,4", "a,b,c", 256, -1, 999, "²", "٤"],
)
def test_resolve_color_rejects_bad_values(color: Color) -> None:
    # The "r,g,b" string cases ("1,2", "1,2,3,4") drive the same wrong-length
    # guard in _resolve_rgb that a native wrong-length (r,g,b) tuple would hit,
    # so a malformed tuple is a clean ColorError, not a later unpack ValueError.
    with pytest.raises(ColorError):
        _ = resolve_color(color)


def test_resolve_color_rejects_bool() -> None:
    # bool is an int subclass, so guard it: True/False are not palette indices.
    for value in (True, False):
        with pytest.raises(ColorError):
            _ = resolve_color(value)
    with pytest.raises(ColorError):
        _ = resolve_color((True, 0, 0))


def test_resolve_color_rejects_rgb_out_of_range() -> None:
    with pytest.raises(ColorError):
        _ = resolve_color((256, 0, 0))


@pytest.mark.parametrize("bad", [(1.5, 0, 0), ("a", 0, 0), (1, 2), (1, 2, 3, 4)])
def test_resolve_rgb_guards_untrusted_tuples(bad: tuple[object, ...]) -> None:
    # _resolve_rgb defends against tuples the public Color type forbids but an
    # untyped runtime caller could pass: non-int channels and wrong lengths are a
    # clean ColorError, never malformed SGR or a downstream TypeError/ValueError.
    with pytest.raises(ColorError):
        _ = _resolve_rgb(bad)


def test_color_error_carries_the_offending_value() -> None:
    with pytest.raises(ColorError) as excinfo:
        _ = resolve_color("bleu")
    assert excinfo.value.value == "bleu"
    assert "bleu" in str(excinfo.value)


def test_ansi_default_colors_equal_the_shared_prefix() -> None:
    # Passing the default palette indices reproduces ANSI_PREFIX byte-for-byte,
    # so the no-argument default path is unchanged.
    matrix = _matrix([[True, False], [False, True]])
    explicit = render_matrix(matrix, mode=RenderMode.ANSI, dark=ANSI_FG, light=ANSI_BG)
    assert explicit == render_matrix(matrix, mode=RenderMode.ANSI)
    assert ANSI_PREFIX in explicit


def test_ansi_named_colors_emit_palette_sgr() -> None:
    matrix = _matrix([[True, False], [False, True]])
    out = render_matrix(matrix, mode=RenderMode.ANSI, dark="red", light="white")
    assert out == f"\x1b[38;5;1;48;5;7m▀▄{ANSI_RESET}"


def test_ansi_truecolor_hex_and_tuple_emit_rgb_sgr() -> None:
    matrix = _matrix([[True, False], [False, True]])
    out = render_matrix(matrix, mode=RenderMode.ANSI, dark="#ff8800", light=(0, 17, 34))
    assert out == f"\x1b[38;2;255;136;0;48;2;0;17;34m▀▄{ANSI_RESET}"


def test_ansi_dark_only_keeps_default_light() -> None:
    out = render_matrix(_matrix([[True]]), mode=RenderMode.ANSI, dark="red")
    assert out == f"\x1b[38;5;1;48;5;{ANSI_BG}m▀{ANSI_RESET}"


def test_ansi_light_only_keeps_default_dark() -> None:
    out = render_matrix(_matrix([[True]]), mode=RenderMode.ANSI, light="black")
    assert out == f"\x1b[38;5;{ANSI_FG};48;5;0m▀{ANSI_RESET}"


@pytest.mark.parametrize("mode", [RenderMode.HALF, RenderMode.BLOCK])
def test_colors_rejected_for_non_ansi_mode(mode: RenderMode) -> None:
    matrix = _matrix([[True, False]])
    with pytest.raises(ColorError):
        _ = render_matrix(matrix, mode=mode, dark="red")
    with pytest.raises(ColorError):
        _ = render_matrix(matrix, mode=mode, light="red")


def test_check_color_mode_allows_no_colors_for_any_mode() -> None:
    for mode in RenderMode:
        check_color_mode(mode, None, None)  # no raise


def test_check_color_mode_allows_colors_for_ansi() -> None:
    check_color_mode(RenderMode.ANSI, "red", "white")  # no raise


def test_check_color_mode_rejects_light_only_for_non_ansi() -> None:
    with pytest.raises(ColorError):
        check_color_mode(RenderMode.HALF, None, "red")


# ── svg ──────────────────────────────────────────────────────────


def test_svg_is_well_formed_and_scaled() -> None:
    matrix = QRMatrix.encode("HELLO")
    root = ET.fromstring(render_svg(matrix, scale=4))
    assert root.attrib["width"] == str(matrix.width * 4)
    assert root.attrib["height"] == str(matrix.height * 4)
    assert root.attrib["viewBox"] == f"0 0 {matrix.width} {matrix.height}"


def test_svg_default_scale() -> None:
    matrix = QRMatrix.encode("HI")
    root = ET.fromstring(render_svg(matrix))
    assert root.attrib["width"] == str(matrix.width * DEFAULT_SCALE)


def test_svg_invert_equals_rendering_the_inverted_matrix() -> None:
    matrix = QRMatrix.encode("HELLO")
    assert render_svg(matrix, invert=True) == render_svg(matrix.inverted())


def test_svg_path_has_one_command_per_dark_module() -> None:
    matrix = _matrix([[True, False], [False, True]])
    assert render_svg(matrix).count("M") == 2


def test_svg_all_light_matrix_has_empty_path() -> None:
    assert 'd=""' in render_svg(_matrix([[False, False], [False, False]]))


@pytest.mark.parametrize("scale", [0, -1])
def test_svg_rejects_non_positive_scale(scale: int) -> None:
    with pytest.raises(CuereError):
        _ = render_svg(QRMatrix.encode("HI"), scale=scale)


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
