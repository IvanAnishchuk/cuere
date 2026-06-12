"""High-level terminal API: render, show, fits."""

from __future__ import annotations

import os
import shutil
import sys
import warnings
from typing import TYPE_CHECKING, Literal

from cuere.errors import WidthError
from cuere.matrix import ECLevel, QRMatrix, coerce
from cuere.render import RenderMode, render_matrix, render_width

if TYPE_CHECKING:
    from typing import IO

OnTooWide = Literal["error", "warn", "render"]


def render(
    data: str | bytes | QRMatrix,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
) -> str:
    """Encode ``data`` (unless it is already a :class:`QRMatrix`) and render it."""
    matrix = coerce(data, border=border, error=error)
    return render_matrix(matrix, mode=RenderMode(mode), invert=invert)


def fits(
    data: str | bytes | QRMatrix,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
    width: int | None = None,
) -> bool:
    """Whether the rendered code fits in ``width`` (default: current terminal)."""
    matrix = coerce(data, border=border, error=error)
    available = width if width is not None else shutil.get_terminal_size().columns
    return render_width(matrix, RenderMode(mode)) <= available


def show(
    data: str | bytes | QRMatrix,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
    out: IO[str] | None = None,
    width: int | None = None,
    on_too_wide: OnTooWide = "error",
    force: bool = False,
) -> None:
    """Render ``data`` and write it to ``out`` (default ``sys.stdout``).

    ANSI mode silently falls back to HALF when ``NO_COLOR`` is set or the
    stream is not a tty, unless ``force=True``: raw SGR codes in logs or
    pipelines are worse than a theme-dependent code.
    """
    stream = out if out is not None else sys.stdout
    matrix = coerce(data, border=border, error=error)
    render_mode = RenderMode(mode)
    if render_mode is RenderMode.ANSI and not force and not _ansi_ok(stream):
        render_mode = RenderMode.HALF
    required = render_width(matrix, render_mode)
    available = width if width is not None else shutil.get_terminal_size().columns
    if required > available:
        if on_too_wide == "error":
            raise WidthError(required, available)
        if on_too_wide == "warn":
            warnings.warn(
                f"QR code needs {required} columns but only {available} are available;"
                + " it will probably not scan",
                stacklevel=2,
            )
    _ = stream.write(render_matrix(matrix, mode=render_mode, invert=invert) + "\n")


def _ansi_ok(stream: IO[str]) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(isatty is not None and isatty())
