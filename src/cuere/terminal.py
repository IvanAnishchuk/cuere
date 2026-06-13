"""High-level terminal API: render, show, fits."""

import os
import shutil
import sys
import warnings
from typing import IO, Literal

from cuere.errors import WidthError
from cuere.matrix import ECLevel, QRMatrix, coerce
from cuere.render import RenderMode, coerce_mode, render_height, render_matrix, render_width

OnTooWide = Literal["error", "warn", "render"]


def render(
    data: str | bytes | QRMatrix,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
    micro: bool = False,
    boost_error: bool = False,
) -> str:
    """Encode ``data`` (unless it is already a :class:`QRMatrix`) and render it."""
    matrix = coerce(data, border=border, error=error, micro=micro, boost_error=boost_error)
    return render_matrix(matrix, mode=coerce_mode(mode), invert=invert)


def fits(
    data: str | bytes | QRMatrix,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
    micro: bool = False,
    boost_error: bool = False,
    width: int | None = None,
    height: int | None = None,
) -> bool:
    """Whether the rendered code fits the terminal in both dimensions.

    Width is the hard constraint (wrapping destroys a scan); height is checked
    too because a code taller than the screen scrolls out of view. ``width``
    and ``height`` default to the current terminal size.
    """
    matrix = coerce(data, border=border, error=error, micro=micro, boost_error=boost_error)
    render_mode = coerce_mode(mode)
    size = shutil.get_terminal_size()
    cols = width if width is not None else size.columns
    rows = height if height is not None else size.lines
    return render_width(matrix, render_mode) <= cols and render_height(matrix, render_mode) <= rows


def show(
    data: str | bytes | QRMatrix,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
    micro: bool = False,
    boost_error: bool = False,
    out: IO[str] | None = None,
    width: int | None = None,
    on_too_wide: OnTooWide = "error",
    force: bool = False,
) -> None:
    """Render ``data`` and write it to ``out`` (default ``sys.stdout``).

    The fit check is width-only: wrapping destroys a code, but a code taller
    than the terminal merely scrolls and stays scannable, so height is not
    gated here (use :func:`fits` for a height-aware predicate).

    ANSI mode silently falls back to HALF when ``NO_COLOR`` is set or the
    stream is not a tty, unless ``force=True``: raw SGR codes in logs or
    pipelines are worse than a theme-dependent code.
    """
    stream = out if out is not None else sys.stdout
    matrix = coerce(data, border=border, error=error, micro=micro, boost_error=boost_error)
    render_mode = coerce_mode(mode)
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
    # Per https://no-color.org/, NO_COLOR disables color whenever it is
    # present, regardless of its value (including the empty string).
    if "NO_COLOR" in os.environ:
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(isatty is not None and isatty())
