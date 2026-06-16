"""Glyph renderers: pure stdlib, deterministic, no terminal interaction.

The HALF mode reproduces the rendering Claude Code CLI uses for its
remote-connection QR codes: two modules per character cell vertically using
`' '`, `'▀'`, `'▄'`, `'█'`, no colors, quiet zone as real spaces.
"""

import enum

from cuere.errors import ColorError, CuereError
from cuere.matrix import QRMatrix

_HALF_GLYPHS = {
    (False, False): " ",
    (True, False): "▀",  # ▀
    (False, True): "▄",  # ▄
    (True, True): "█",  # █
}
# Spec-correct polarity regardless of terminal theme: dark modules are black
# (color 16) on a white (color 231) background. These two ANSI 256-colors are the
# single source of truth — cuere.rich builds its Style from them too.
ANSI_FG = 16
ANSI_BG = 231
ANSI_PREFIX = f"\x1b[38;5;{ANSI_FG};48;5;{ANSI_BG}m"
ANSI_RESET = "\x1b[0m"

# A terminal color for ANSI mode's `dark` / `light` modules, as resolved by
# resolve_color. One of:
#   * a name - one of the 16 standard ANSI colors ("black", "red", ..., "white"
#     and their "bright_*" variants), matched case- and separator-insensitively;
#   * a palette index - an int in 0-255 (the xterm 256-color palette), or its
#     decimal string form ("16");
#   * a truecolor value - a "#rrggbb" / "#rgb" hex string, an (r, g, b) tuple of
#     0-255 ints, or its "r,g,b" string form.
# A malformed color raises ColorError. (Documented as a leading comment, not a
# docstring, because check-docstring-first rejects a string after a `type` alias.)
type Color = str | int | tuple[int, int, int]

_MAX_COLOR = 255  # palette-index / channel ceiling
_RGB_CHANNELS = 3  # an (r, g, b) triple; also a "#rgb" shorthand's digit count

# The 16 standard ANSI color names, mapped to their xterm palette index. Indices
# 0-15 are the terminal's themeable base colors; the renderer *defaults*
# (ANSI_FG / ANSI_BG above) deliberately use the fixed 16-255 cube instead, so a
# named "black"/"white" is a different, theme-dependent choice the caller opts
# into. Names are matched after lower-casing and folding spaces/hyphens to "_".
_NAMED_COLORS: dict[str, int] = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7,
    "bright_black": 8,
    "bright_red": 9,
    "bright_green": 10,
    "bright_yellow": 11,
    "bright_blue": 12,
    "bright_magenta": 13,
    "bright_cyan": 14,
    "bright_white": 15,
}

_BAD_COLOR_BOOL = "color must not be a bool"
_BAD_COLOR_INDEX = "color index out of range 0-255"
_BAD_COLOR_NAME = "not a known color name"
_BAD_COLOR_HEX = "not a valid #rgb / #rrggbb hex color"
_BAD_COLOR_RGB = "rgb color must be three integers in 0-255"
_COLOR_NEEDS_ANSI = "dark/light colors require mode 'ansi'"


def resolve_color(color: Color) -> int | tuple[int, int, int]:
    """Normalize a `Color` to a palette index or an `(r, g, b)` triple.

    The single validation/normalization point, so the SGR text path
    (`render_matrix`) and the Rich path (`cuere.rich.QRCode`) agree.
    Raises `ColorError` on anything malformed.
    """
    if isinstance(color, bool):  # bool is an int subclass; True/False is not a color
        raise ColorError(_BAD_COLOR_BOOL, color)
    if isinstance(color, int):
        return _check_index(color, color)
    if isinstance(color, tuple):
        return _resolve_rgb(color)
    return _resolve_str(color)


def _check_index(index: int, original: object) -> int:
    if not 0 <= index <= _MAX_COLOR:
        raise ColorError(_BAD_COLOR_INDEX, original)
    return index


def _resolve_rgb(color: tuple[object, ...]) -> tuple[int, int, int]:
    # Validates untrusted input fully — length, integer type, and range — so any
    # malformed tuple is a clean ColorError rather than an unpack ValueError,
    # malformed SGR, or a TypeError downstream. The public Color type documents
    # the intent (three 0-255 ints) but cannot enforce it for an untyped caller,
    # so this guards it instead of trusting the annotation.
    if len(color) != _RGB_CHANNELS:
        raise ColorError(_BAD_COLOR_RGB, color)
    channels: list[int] = []
    for channel in color:
        if isinstance(channel, bool):  # bool is an int subclass, not a channel value
            raise ColorError(_BAD_COLOR_BOOL, color)
        if not isinstance(channel, int) or not 0 <= channel <= _MAX_COLOR:
            raise ColorError(_BAD_COLOR_RGB, color)
        channels.append(channel)
    return (channels[0], channels[1], channels[2])


def _resolve_str(color: str) -> int | tuple[int, int, int]:
    text = color.strip()
    if text.startswith("#"):
        return _resolve_hex(text, color)
    if "," in text:
        return _resolve_csv(text, color)
    if text.isascii() and text.isdigit():  # ASCII-only: "²"/"٤" are not indices
        return _check_index(int(text), color)
    index = _NAMED_COLORS.get(text.lower().replace(" ", "_").replace("-", "_"))
    if index is None:
        raise ColorError(_BAD_COLOR_NAME, color)
    return index


def _resolve_hex(text: str, original: str) -> tuple[int, int, int]:
    digits = text[1:]
    if len(digits) == _RGB_CHANNELS:  # "#rgb" shorthand -> "#rrggbb"
        digits = "".join(channel * 2 for channel in digits)
    try:
        red, green, blue = bytes.fromhex(digits)  # validates hex + exactly 3 bytes
    except ValueError:
        raise ColorError(_BAD_COLOR_HEX, original) from None
    return (red, green, blue)


def _resolve_csv(text: str, original: str) -> tuple[int, int, int]:
    try:
        channels = tuple(int(part) for part in text.split(","))
    except ValueError:
        raise ColorError(_BAD_COLOR_RGB, original) from None
    return _resolve_rgb(channels)


def _sgr_color(resolved: int | tuple[int, int, int], *, background: bool) -> str:
    """Build the SGR parameters selecting `resolved` as a foreground/background."""
    lead = 48 if background else 38
    if isinstance(resolved, int):
        return f"{lead};5;{resolved}"
    red, green, blue = resolved
    return f"{lead};2;{red};{green};{blue}"


def resolve_pair(
    dark: Color | None, light: Color | None
) -> tuple[int | tuple[int, int, int], int | tuple[int, int, int]]:
    """Resolve `(dark, light)`, filling each `None` with its theme-proof default.

    The single place ANSI mode's default ink/ground (palette `ANSI_FG` /
    `ANSI_BG`) is applied, so the SGR text path (`render_matrix`) and the
    Rich path (`cuere.rich.QRCode`) never disagree on either the colors or
    the defaults.
    """
    return (
        resolve_color(dark if dark is not None else ANSI_FG),
        resolve_color(light if light is not None else ANSI_BG),
    )


# Defaults for the pixel-grid renderers (SVG here, PNG in cuere.output): one
# module is a square, black on white. DEFAULT_SCALE is pixels per module.
DEFAULT_SCALE = 10
SVG_DARK = "#000000"
SVG_LIGHT = "#ffffff"
_INVALID_SCALE = "scale must be a positive integer (pixels per module)"


def check_scale(scale: int) -> None:
    """Reject a non-positive pixels-per-module `scale`.

    A zero or negative scale would yield a blank or negatively-sized image, so
    it raises a `CuereError` (never a bare `ValueError`),
    keeping the contract the rest of the API holds.
    """
    if scale < 1:
        raise CuereError(_INVALID_SCALE)


class RenderMode(enum.StrEnum):
    """How a QR matrix is turned into text.

    Example:

    ```python
    from cuere import RenderMode, render

    render("HELLO", mode=RenderMode.BLOCK)   # or just mode="block"
    ```
    """

    HALF = "half"
    """Unicode half-blocks, 1 column x 1/2 row per module (default)."""
    BLOCK = "block"
    """Two full-width chars per module: most robust glyphs, twice as wide."""
    ANSI = "ansi"
    """HALF glyphs with forced black-on-white SGR colors: theme-proof."""


def coerce_mode(mode: RenderMode | str) -> RenderMode:
    """Convert a mode name to `RenderMode`, raising on an unknown value.

    Keeps the public API's error contract consistent: an invalid `mode`
    raises `CuereError`, just like an invalid `error`
    level or `border` does, rather than a bare `ValueError`.
    """
    try:
        return RenderMode(mode)
    except ValueError as exc:  # e.g. "'sixel' is not a valid RenderMode"
        raise CuereError(str(exc)) from exc


def check_color_mode(mode: RenderMode, dark: Color | None, light: Color | None) -> None:
    """Reject `dark` / `light` colors for a mode that emits none.

    Only ANSI mode carries SGR colors; the plain glyph modes (`half` / `block`)
    inherit the terminal's own colors, so a color there would be silently dropped.
    Asking for one is an error, not a no-op — raising
    `ColorError` keeps the contract explicit.
    """
    if (dark is not None or light is not None) and mode is not RenderMode.ANSI:
        raise ColorError(_COLOR_NEEDS_ANSI, mode)


def render_matrix(
    matrix: QRMatrix,
    *,
    mode: RenderMode = RenderMode.HALF,
    invert: bool = False,
    dark: Color | None = None,
    light: Color | None = None,
) -> str:
    """Render `matrix` as text; lines are equal-width, no trailing newline.

    The quiet zone is rendered as part of the output (spaces / light modules)
    because a scanner needs it in the code's own background, not whatever the
    surrounding terminal happens to show.

    `dark` / `light` customize the SGR colors of ANSI mode (dark modules and
    the light ground respectively); they default to the theme-proof black-on-white
    (palette `16` on `231`). They are only valid for `mode="ansi"` — passing
    a color for `half` / `block` raises `ColorError`.

    Example:

    ```python
    from cuere import QRMatrix, RenderMode, render_matrix

    m = QRMatrix.encode("HELLO")
    plain = render_matrix(m)  # default half-blocks
    colored = render_matrix(m, mode=RenderMode.ANSI, dark="cyan")  # custom ANSI ink
    ```
    """
    check_color_mode(mode, dark, light)
    if invert:
        matrix = matrix.inverted()
    if mode is RenderMode.BLOCK:
        lines = ["".join("██" if m else "  " for m in row) for row in matrix.modules]
    else:
        lines = _half_lines(matrix)
        if mode is RenderMode.ANSI:
            fg, bg = resolve_pair(dark, light)
            prefix = f"\x1b[{_sgr_color(fg, background=False)};{_sgr_color(bg, background=True)}m"
            lines = [f"{prefix}{line}{ANSI_RESET}" for line in lines]
    return "\n".join(lines)


def render_svg(matrix: QRMatrix, *, scale: int = DEFAULT_SCALE, invert: bool = False) -> str:
    """Render `matrix` as a standalone SVG document, one module per unit.

    Dark modules become a single `<path>` over a light background `<rect>`.
    `viewBox` is the module grid, so the path coordinates stay small integers;
    `width`/`height` scale it to `scale` pixels per module.
    `shape-rendering="crispEdges"` keeps module borders sharp (anti-aliasing
    blur hurts scanning). `invert` flips dark and light via
    `matrix.inverted()` — the same single code path the glyph renderers use.

    Example:

    ```python
    from cuere import QRMatrix, render_svg

    svg = render_svg(QRMatrix.encode("HELLO"), scale=8)
    with open("hello.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    ```
    """
    check_scale(scale)
    if invert:
        matrix = matrix.inverted()
    cols, rows = matrix.width, matrix.height
    path = "".join(
        f"M{x} {y}h1v1h-1z"
        for y, row in enumerate(matrix.modules)
        for x, dark in enumerate(row)
        if dark
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols * scale}"'
        f' height="{rows * scale}" viewBox="0 0 {cols} {rows}" shape-rendering="crispEdges">\n'
        f'<rect width="{cols}" height="{rows}" fill="{SVG_LIGHT}"/>\n'
        f'<path d="{path}" fill="{SVG_DARK}"/>\n'
        "</svg>\n"
    )


def render_width(matrix: QRMatrix, mode: RenderMode = RenderMode.HALF) -> int:
    """Terminal columns the rendered matrix occupies (ignoring SGR codes).

    Example:

    ```python
    from cuere import QRMatrix, render_width, render_height

    m = QRMatrix.encode("HELLO")
    cols, rows = render_width(m), render_height(m)   # half-block footprint
    ```
    """
    return matrix.width * 2 if mode is RenderMode.BLOCK else matrix.width


def render_height(matrix: QRMatrix, mode: RenderMode = RenderMode.HALF) -> int:
    """Terminal rows the rendered matrix occupies.

    Example:

    ```python
    from cuere import QRMatrix, RenderMode, render_height

    rows = render_height(QRMatrix.encode("HELLO"), mode=RenderMode.BLOCK)
    ```
    """
    if mode is RenderMode.BLOCK:
        return matrix.height
    return (matrix.height + 1) // 2


def _half_lines(matrix: QRMatrix) -> list[str]:
    rows = matrix.modules
    lines: list[str] = []
    for i in range(0, len(rows), 2):
        top = rows[i]
        # An odd-height matrix gets a virtual light bottom row.
        bottom = rows[i + 1] if i + 1 < len(rows) else tuple(False for _ in top)
        lines.append("".join(_HALF_GLYPHS[top_bot] for top_bot in zip(top, bottom, strict=True)))
    return lines
