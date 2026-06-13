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
# (color 16) on a white (color 231) background.
ANSI_PREFIX = "\x1b[38;5;16;48;5;231m"
ANSI_RESET = "\x1b[0m"


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
