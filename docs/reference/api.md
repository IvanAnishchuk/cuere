# API reference

The public API of `cuere`. Everything here is re-exported from the top-level
`cuere` package (see `cuere.__all__`); the canonical module is shown for each
symbol. Each entry is rendered from its source docstring.

## Terminal API

The high-level entry points.

::: cuere.terminal.render

::: cuere.terminal.show

::: cuere.terminal.fits

::: cuere.terminal.SupportsWrite

## Matrix & encoding

::: cuere.matrix.QRMatrix

::: cuere.matrix.ECLevel

## Rendering

::: cuere.render.RenderMode

::: cuere.render.render_matrix

::: cuere.render.render_svg

::: cuere.render.render_width

::: cuere.render.render_height

::: cuere.render.Color

A terminal color for ANSI mode's `dark` / `light` modules. One of:

- a **name** — one of the 16 standard ANSI colors (`"black"`, `"red"`, …,
  `"white"` and their `"bright_*"` variants), matched case- and
  separator-insensitively;
- a **palette index** — an int in 0–255 (the xterm 256-color cube), or its
  decimal string form (`"16"`);
- a **truecolor** value — a `"#rrggbb"` / `"#rgb"` hex string, an `(r, g, b)`
  tuple of 0–255 ints, or its `"r,g,b"` string form.

A malformed color raises [`ColorError`](#cuere.errors.ColorError).

```python
from cuere import render

render("HI", mode="ansi", dark="cyan", light="black")     # named
render("HI", mode="ansi", dark=16, light=231)             # palette index
render("HI", mode="ansi", dark="#00ffaa", light=(0, 0, 0))  # truecolor
```

## Output formats

::: cuere.output.OutputFormat

::: cuere.output.render_bytes

::: cuere.output.save

::: cuere.output.SupportsWriteBytes

## Wallet URIs

::: cuere.wallet.bitcoin_uri

::: cuere.wallet.lightning_uri

::: cuere.wallet.ethereum_uri

::: cuere.wallet.erc20_transfer_uri

::: cuere.wallet.optimize_uri

::: cuere.wallet.scheme_case

::: cuere.wallet.SchemeCase

::: cuere.wallet.is_qr_alphanumeric

## Rich integration

::: cuere.rich.QRCode

## Exceptions

::: cuere.errors.CuereError

::: cuere.errors.EncodingError

::: cuere.errors.WidthError

::: cuere.errors.ColorError

::: cuere.errors.WalletURIError

::: cuere.errors.UnknownFormatError

::: cuere.errors.MissingDependencyError
