"""Output-format dispatch: render a QR code to bytes or a file.

`render_bytes` is the primitive — it returns the encoded `bytes` for a
named `OutputFormat`; `save` is the file-and-stream convenience
that can also infer the format from a path suffix. `text` is the terminal
glyph rendering (UTF-8, honoring `mode`); `svg` is a vector document; and
`png` is a raster image that needs the optional `cuere[image]` extra
(Pillow), imported lazily so `import cuere` never pulls it in.
"""

import enum
import io
import os
from pathlib import Path
from typing import Protocol, Unpack, runtime_checkable

from cuere.errors import MissingDependencyError, UnknownFormatError
from cuere.matrix import Encodable, EncodeOptions, QRMatrix, coerce
from cuere.render import (
    DEFAULT_SCALE,
    RenderMode,
    check_scale,
    coerce_mode,
    render_matrix,
    render_svg,
)


class OutputFormat(enum.StrEnum):
    """A target format for `render_bytes` / `save`.

    Example:

    ```python
    import io

    from cuere import OutputFormat, save

    stream = io.BytesIO()
    save("HELLO", "out.svg")  # inferred from the suffix
    save("HELLO", stream, format=OutputFormat.SVG)  # a stream has no suffix, be explicit
    ```
    """

    TEXT = "text"
    """The terminal glyph rendering (honors `mode`/`invert`), UTF-8 bytes."""
    SVG = "svg"
    """A standalone SVG vector document, UTF-8 bytes."""
    PNG = "png"
    """A PNG raster image; requires the optional `cuere[image]` extra."""


@runtime_checkable
class SupportsWriteBytes(Protocol):
    """A binary sink: any object with a `write(bytes)` method.

    The byte-oriented counterpart to `cuere.terminal.SupportsWrite`;
    `sys.stdout.buffer`, `io.BytesIO`, and an open binary file all qualify.
    Runtime-checkable so `save` can tell a stream from a path — neither
    `str` nor `os.PathLike` carries a `write` method.

    Example:

    ```python
    import io
    from cuere import save

    buf = io.BytesIO()              # any object with .write(bytes) qualifies
    save("HELLO", buf, format="svg")
    ```
    """

    def write(self, b: bytes, /) -> object:
        """Write `b` to the sink; the return value is ignored."""


# The optional-extra name and the suffix→format map, kept as module-level
# Name references so raise sites never pass a string literal (ruff TRY003).
_IMAGE_EXTRA = "image"
_SUFFIX_FORMATS = {
    ".txt": OutputFormat.TEXT,
    ".svg": OutputFormat.SVG,
    ".png": OutputFormat.PNG,
}
_UNKNOWN_FORMAT_HINT = "unknown output format; choose from " + ", ".join(
    fmt.value for fmt in OutputFormat
)
_NO_FORMAT_HINT = "cannot infer output format; pass format= or use a known file suffix"


def coerce_format(fmt: OutputFormat | str) -> OutputFormat:
    """Convert a format name to `OutputFormat`, raising on an unknown one.

    Mirrors `cuere.render.coerce_mode`: an invalid value raises
    `UnknownFormatError` (a `CuereError`), never a
    bare `ValueError`.
    """
    try:
        return OutputFormat(fmt)
    except ValueError as exc:
        raise UnknownFormatError(fmt, _UNKNOWN_FORMAT_HINT) from exc


def render_bytes(
    data: Encodable,
    *,
    format: OutputFormat | str = OutputFormat.TEXT,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    scale: int = DEFAULT_SCALE,
    **options: Unpack[EncodeOptions],
) -> bytes:
    """Encode `data` and render it to `bytes` in `format`.

    `mode` selects the glyphs for the `text` format and is ignored by the
    image formats; `scale` is pixels-per-module for `svg`/`png` and is
    ignored by `text`. Encoding keywords (`error`/`border`/…) apply only
    when `data` is not already a `QRMatrix`.

    Example:

    ```python
    from cuere import render_bytes

    svg = render_bytes("HELLO", format="svg")   # UTF-8 bytes
    png = render_bytes("HELLO", format="png")   # needs cuere[image]
    ```
    """
    matrix = coerce(data, **options)
    fmt = coerce_format(format)
    if fmt is OutputFormat.TEXT:
        text = render_matrix(matrix, mode=coerce_mode(mode), invert=invert)
        return (text + "\n").encode("utf-8")
    if fmt is OutputFormat.SVG:
        return render_svg(matrix, scale=scale, invert=invert).encode("utf-8")
    # PNG is the only remaining format; a new OutputFormat must add its branch
    # above (every member is exercised by tests, so a missing branch is caught).
    return _render_png(matrix, scale=scale, invert=invert)


def save(
    data: Encodable,
    dest: str | os.PathLike[str] | SupportsWriteBytes,
    *,
    format: OutputFormat | str | None = None,
    mode: RenderMode | str = RenderMode.HALF,
    invert: bool = False,
    scale: int = DEFAULT_SCALE,
    **options: Unpack[EncodeOptions],
) -> None:
    """Render `data` and write the bytes to `dest`.

    `dest` is a filesystem path or an open binary stream. When `format` is
    omitted it is inferred from a path's suffix (`.txt`/`.svg`/`.png`); a
    stream needs an explicit `format`. Unknown formats and unguessable
    destinations raise `UnknownFormatError`.

    Example:

    ```python
    from cuere import save

    save("HELLO", "qr.png")              # format from the .png suffix
    with open("qr.svg", "wb") as fh:
        save("HELLO", fh, format="svg")  # a stream needs an explicit format
    ```
    """
    fmt = _resolve_format(format, dest)
    payload = render_bytes(data, format=fmt, mode=mode, invert=invert, scale=scale, **options)
    if isinstance(dest, SupportsWriteBytes):
        _ = dest.write(payload)
    else:
        _ = Path(dest).write_bytes(payload)


def _resolve_format(
    format: OutputFormat | str | None,
    dest: str | os.PathLike[str] | SupportsWriteBytes,
) -> OutputFormat:
    if format is not None:
        return coerce_format(format)
    if isinstance(dest, SupportsWriteBytes):  # a stream carries no inferable suffix
        raise UnknownFormatError(dest, _NO_FORMAT_HINT)
    suffix = Path(dest).suffix.lower()
    if suffix in _SUFFIX_FORMATS:
        return _SUFFIX_FORMATS[suffix]
    raise UnknownFormatError(suffix or os.fspath(dest), _NO_FORMAT_HINT)


def _render_png(matrix: QRMatrix, *, scale: int, invert: bool) -> bytes:
    check_scale(scale)
    # Pillow is the optional, heavy cuere[image] dependency, imported lazily
    # here (not at module top) so `import cuere` never pulls it in and PNG fails
    # with a clean MissingDependencyError when the extra is not installed.
    try:
        from PIL import Image  # noqa: PLC0415 — heavy optional dep, must stay lazy
    except ImportError as exc:
        raise MissingDependencyError(OutputFormat.PNG, _IMAGE_EXTRA) from exc
    if invert:
        matrix = matrix.inverted()
    cols, rows = matrix.width, matrix.height
    # Expand each module to a square block of side `scale` (L-mode pixels,
    # dark=0, light=255) directly, so the integer upscale needs no resampling.
    lines = [
        b"".join((b"\x00" if dark else b"\xff") * scale for dark in row) for row in matrix.modules
    ]
    pixels = b"".join(line * scale for line in lines)
    image = Image.frombytes("L", (cols * scale, rows * scale), pixels)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
