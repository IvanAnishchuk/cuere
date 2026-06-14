# Output formats

cuere draws QR codes in the terminal by default, but the same matrix can be
rendered to a file or to raw bytes in several formats. This is the model behind
[`cuere.output`](../src/cuere/output.py) and the CLI `--output` option.

## Two entry points

| Function | Returns | Use it when |
|---|---|---|
| `render_bytes(data, *, format=…, …)` | `bytes` | you want the bytes (to upload, attach, embed) |
| `save(data, dest, *, format=None, …)` | `None` | you want them written to a path or stream |

`save` is a thin convenience over `render_bytes`: it resolves the format, renders
the bytes, then writes them. Everything `render_bytes` accepts, `save` accepts.

```python
from cuere import render_bytes, save

data = render_bytes("HELLO", format="svg")   # -> bytes
save("HELLO", "code.svg")                     # writes the same bytes to a file
```

Both take a payload (`str` / `bytes` / a pre-built `QRMatrix`) and forward the
usual encoding knobs (`error`, `border`, `micro`, `boost_error`) and `invert`,
identically to `render` / `show`.

## Formats

`OutputFormat` is the set of targets. Names are lowercase strings, so you can
pass either the enum or the string:

| `OutputFormat` | name | bytes are | notes |
|---|---|---|---|
| `TEXT` | `"text"` | UTF-8 text | the terminal glyph rendering; honors `mode` |
| `SVG` | `"svg"` | UTF-8 text | a standalone vector document |
| `PNG` | `"png"` | binary | a raster image; needs the `cuere[image]` extra |

- **text** is exactly what `render()` produces (default `half` glyphs; `mode`
  selects `half` / `block` / `ansi`), with a trailing newline, UTF-8 encoded.
- **svg** is a self-contained `<svg>` document — one `<path>` of dark modules
  over a light background `<rect>`, `shape-rendering="crispEdges"` so module
  borders stay sharp. It is pure stdlib (no dependency) and also available
  directly as `render_svg()`.
- **png** is a raster grid built with [Pillow](https://python-pillow.org/).

### `scale`

For the image formats, `scale` is the number of pixels per QR module (default
`10`). SVG carries it as the `width` / `height` while keeping a module-unit
`viewBox` (so it stays resolution-independent); PNG expands each module into a
`scale × scale` block of pixels. `text` ignores `scale`; the image formats
ignore `mode`.

```python
render_bytes("HELLO", format="png", scale=4)   # 4 px per module
```

## Choosing the destination (`save`)

`save` writes to a filesystem path or to an open **binary** stream:

```python
from io import BytesIO

save("HELLO", "code.png")          # a path (str or os.PathLike)
save("HELLO", BytesIO(), format="png")   # a binary stream (SupportsWriteBytes)
```

When `format` is omitted it is inferred from the path suffix:

| suffix | format |
|---|---|
| `.txt` | text |
| `.svg` | svg |
| `.png` | png |

A stream has no suffix, so writing to one **requires** an explicit `format`. An
unguessable destination (unknown suffix, or a stream with no `format`) raises
`UnknownFormatError`.

`SupportsWriteBytes` is the byte-oriented sink protocol (anything with
`write(bytes)` — `sys.stdout.buffer`, `io.BytesIO`, an open binary file); it is
the counterpart to `terminal.SupportsWrite`.

## Errors

Both are `CuereError` subclasses, so a single `except CuereError` covers them
(and they never leak a bare `ValueError`):

- **`UnknownFormatError`** — an unrecognized format name, or a destination whose
  format can't be inferred. The message lists the known formats.
- **`MissingDependencyError`** — a format needs an optional dependency that is
  not installed (today: PNG without `cuere[image]`). The message names the extra
  to install.

## The `cuere[image]` extra

PNG is the one format with a runtime dependency. Pillow is heavy and only needed
for raster output, so it is an opt-in [extra](https://peps.python.org/pep-0508/),
imported lazily inside the PNG renderer — `import cuere` never imports Pillow,
and text / SVG export work without it.

```bash
pip install 'cuere[image]'    # or: uv add 'cuere[image]'
```

## CLI

`--output FORMAT[:PATH]` selects a format and destination; `--scale` sets the
pixels-per-module. Omitting `--output` keeps the default terminal rendering with
its terminal-only heuristics: the width check (`--check-width`), and the
`NO_COLOR` / tty ANSI fallback (`--force`). `--output` instead emits the chosen
format's bytes verbatim — including `--output text`, which writes exactly the
`--mode` rendering — so those heuristics do not apply on this path (the bytes may
not be going to a terminal at all).

```bash
cuere HELLO --output svg:code.svg          # write SVG to code.svg
cuere HELLO -o png:art.png --scale 12      # write a 12-px-per-module PNG
cuere HELLO --output png:-  > code.png     # PATH '-' (or omitted) is stdout
cuere HELLO --output text                  # the terminal rendering, to stdout
```

An unknown format or a missing extra surfaces as a clean `error: …` (exit 1),
the same as any other CLI error.
