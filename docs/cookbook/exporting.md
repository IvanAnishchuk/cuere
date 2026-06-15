# Exporting QR codes (SVG, PNG)

Recipes for getting a QR code out of the terminal and into a file or a byte
buffer. For the full output model — formats, the dispatcher, the CLI surface —
see [output formats](../output-formats.md).

## Save a QR code to a file

[`save`](../../src/cuere/output.py) renders any payload to a file. The format is
taken from the path suffix (`.svg`, `.png`, `.txt`), so the common case needs no
extra arguments:

```python
from cuere import save

save("bitcoin:BC1Q...", "invoice.svg")            # vector, infinite resolution
save("bitcoin:BC1Q...", "invoice.png", scale=8)   # 8 pixels per module
```

`scale` is pixels-per-module for the image formats (SVG scales its `width` /
`height`; PNG is a raster grid). For full control over the destination, pass an
explicit `format` (overriding the suffix) or write to an open binary stream:

```python
from io import BytesIO

from cuere import save

save("HELLO", "code.dat", format="svg")   # suffix says nothing; be explicit
buffer = BytesIO()
save("HELLO", buffer, format="png")       # a stream always needs format=
```

Need the bytes without touching the filesystem (to attach, upload, or embed)?
[`render_bytes`](../../src/cuere/output.py) returns them directly:

```python
from cuere import render_bytes

svg = render_bytes("HELLO", format="svg")            # -> bytes (UTF-8 SVG)
png = render_bytes("HELLO", format="png", scale=10)  # -> bytes (PNG image)
```

All the encoding knobs (`error`, `border`, `micro`, `boost_error`) and `invert`
work here too, exactly as in `render` / `show`.

## PNG needs the `cuere[image]` extra

PNG output uses [Pillow](https://python-pillow.org/), which is an optional
dependency to keep the base install lightweight — text and SVG export need
nothing extra. Install it with:

```bash
pip install 'cuere[image]'   # or: uv add 'cuere[image]'
```

Without it, PNG raises a clear `MissingDependencyError` (a `CuereError`); an
unrecognized format name raises `UnknownFormatError`:

```python
from cuere import MissingDependencyError, UnknownFormatError, render_bytes

try:
    render_bytes("HELLO", format="png")     # MissingDependencyError if Pillow absent
    render_bytes("HELLO", format="jpeg")    # UnknownFormatError: not a known format
except (MissingDependencyError, UnknownFormatError) as exc:
    print(exc)
```

From the CLI, the same lives behind `--output FORMAT[:PATH]` (and `--scale`);
`PATH` of `-` or omitted writes to stdout, and omitting `--output` keeps the
default terminal rendering. See [output formats](../output-formats.md) for the
full model.
