"""Glyph renderers: pure stdlib, deterministic, no terminal interaction.

The HALF mode reproduces the rendering Claude Code CLI uses for its
remote-connection QR codes: two modules per character cell vertically using
``' '``, ``'▀'``, ``'▄'``, ``'█'``, no colors, quiet zone as real spaces.
"""

import enum

from cuere.errors import CuereError
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

# Defaults for the pixel-grid renderers (SVG here, PNG in cuere.output): one
# module is a square, black on white. DEFAULT_SCALE is pixels per module.
DEFAULT_SCALE = 10
SVG_DARK = "#000000"
SVG_LIGHT = "#ffffff"
_INVALID_SCALE = "scale must be a positive integer (pixels per module)"


def check_scale(scale: int) -> None:
    """Reject a non-positive pixels-per-module ``scale``.

    A zero or negative scale would yield a blank or negatively-sized image, so
    it raises a :class:`~cuere.errors.CuereError` (never a bare ``ValueError``),
    keeping the contract the rest of the API holds.
    """
    if scale < 1:
        raise CuereError(_INVALID_SCALE)


class RenderMode(enum.StrEnum):
    """How a QR matrix is turned into text."""

    HALF = "half"
    """Unicode half-blocks, 1 column x 1/2 row per module (default)."""
    BLOCK = "block"
    """Two full-width chars per module: most robust glyphs, twice as wide."""
    ANSI = "ansi"
    """HALF glyphs with forced black-on-white SGR colors: theme-proof."""


def coerce_mode(mode: RenderMode | str) -> RenderMode:
    """Convert a mode name to :class:`RenderMode`, raising on an unknown value.

    Keeps the public API's error contract consistent: an invalid ``mode``
    raises :class:`~cuere.errors.CuereError`, just like an invalid ``error``
    level or ``border`` does, rather than a bare ``ValueError``.
    """
    try:
        return RenderMode(mode)
    except ValueError as exc:  # e.g. "'sixel' is not a valid RenderMode"
        raise CuereError(str(exc)) from exc


def render_matrix(
    matrix: QRMatrix,
    *,
    mode: RenderMode = RenderMode.HALF,
    invert: bool = False,
) -> str:
    """Render ``matrix`` as text; lines are equal-width, no trailing newline.

    The quiet zone is rendered as part of the output (spaces / light modules)
    because a scanner needs it in the code's own background, not whatever the
    surrounding terminal happens to show.
    """
    if invert:
        matrix = matrix.inverted()
    if mode is RenderMode.BLOCK:
        lines = ["".join("██" if m else "  " for m in row) for row in matrix.modules]
    else:
        lines = _half_lines(matrix)
        if mode is RenderMode.ANSI:
            lines = [f"{ANSI_PREFIX}{line}{ANSI_RESET}" for line in lines]
    return "\n".join(lines)


def render_svg(matrix: QRMatrix, *, scale: int = DEFAULT_SCALE, invert: bool = False) -> str:
    """Render ``matrix`` as a standalone SVG document, one module per unit.

    Dark modules become a single ``<path>`` over a light background ``<rect>``.
    ``viewBox`` is the module grid, so the path coordinates stay small integers;
    ``width``/``height`` scale it to ``scale`` pixels per module.
    ``shape-rendering="crispEdges"`` keeps module borders sharp (anti-aliasing
    blur hurts scanning). ``invert`` flips dark and light via
    ``matrix.inverted()`` — the same single code path the glyph renderers use.
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
    """Terminal columns the rendered matrix occupies (ignoring SGR codes)."""
    return matrix.width * 2 if mode is RenderMode.BLOCK else matrix.width


def render_height(matrix: QRMatrix, mode: RenderMode = RenderMode.HALF) -> int:
    """Terminal rows the rendered matrix occupies."""
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
