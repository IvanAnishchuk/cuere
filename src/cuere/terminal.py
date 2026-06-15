"""High-level terminal API: render, show, fits."""

import os
import shutil
import sys
import warnings
from typing import Literal, Protocol, Unpack

from cuere.errors import WidthError
from cuere.matrix import Encodable, EncodeOptions, coerce
from cuere.render import (
    Color,
    RenderMode,
    coerce_mode,
    render_height,
    render_matrix,
    render_width,
)

OnTooWide = Literal["error", "warn", "render"]


class SupportsWrite(Protocol):
    """A text sink: any object with a ``write(str)`` method.

    ``show`` writes a single string and probes ``isatty`` defensively via
    ``getattr``, so it needs only this much of a stream — ``sys.stdout``,
    ``io.StringIO``, and minimal write-only wrappers all qualify. This is
    deliberately narrower than ``typing.IO[str]``.
    """

    def write(self, s: str, /) -> object:
        """Write ``s`` to the sink; the return value is ignored."""


def render(
    data: Encodable,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    dark: Color | None = None,
    light: Color | None = None,
    **options: Unpack[EncodeOptions],
) -> str:
    """Encode ``data`` (unless it is already a :class:`QRMatrix`) and render it.

    ``dark`` / ``light`` customize ANSI mode's module colors (see
    :func:`cuere.render.render_matrix`); they are only valid for ``mode="ansi"``.
    """
    matrix = coerce(data, **options)
    return render_matrix(matrix, mode=coerce_mode(mode), invert=invert, dark=dark, light=light)


def fits(
    data: Encodable,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    width: int | None = None,
    height: int | None = None,
    **options: Unpack[EncodeOptions],
) -> bool:
    """Whether the rendered code fits the terminal in both dimensions.

    Width is the hard constraint (wrapping destroys a scan); height is checked
    too because a code taller than the screen scrolls out of view. ``width``
    and ``height`` default to the current terminal size.
    """
    matrix = coerce(data, **options)
    render_mode = coerce_mode(mode)
    size = shutil.get_terminal_size()
    cols = width if width is not None else size.columns
    rows = height if height is not None else size.lines
    return render_width(matrix, render_mode) <= cols and render_height(matrix, render_mode) <= rows


def show(
    data: Encodable,
    *,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    out: SupportsWrite | None = None,
    width: int | None = None,
    on_too_wide: OnTooWide = "error",
    force: bool = False,
    dark: Color | None = None,
    light: Color | None = None,
    **options: Unpack[EncodeOptions],
) -> None:
    """Render ``data`` and write it to ``out`` (default ``sys.stdout``).

    The fit check is width-only: wrapping destroys a code, but a code taller
    than the terminal merely scrolls and stays scannable, so height is not
    gated here (use :func:`fits` for a height-aware predicate).

    ANSI mode silently falls back to HALF when ``NO_COLOR`` is set or the
    stream is not a tty, unless ``force=True``: raw SGR codes in logs or
    pipelines are worse than a theme-dependent code. ``dark`` / ``light``
    customize ANSI mode's colors (only valid for ``mode="ansi"``); when ANSI
    falls back, they are dropped with it so a no-color terminal gets plain glyphs.
    """
    stream = out if out is not None else sys.stdout
    matrix = coerce(data, **options)
    render_mode = coerce_mode(mode)
    if render_mode is RenderMode.ANSI and not force and not _ansi_ok(stream):
        render_mode = RenderMode.HALF
        dark = light = None
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
    _ = stream.write(
        render_matrix(matrix, mode=render_mode, invert=invert, dark=dark, light=light) + "\n"
    )


def _ansi_ok(stream: SupportsWrite) -> bool:
    # Per https://no-color.org/, NO_COLOR disables color whenever it is
    # present, regardless of its value (including the empty string).
    if "NO_COLOR" in os.environ:
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(isatty is not None and isatty())
