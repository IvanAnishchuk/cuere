---
icon: lucide/play
---

# Quickstart

This page takes you from install to a scannable code in a couple of minutes —
in both the library and the CLI. For the full option list see the
[CLI reference](cli-reference.md) and [API reference](reference/api.md).

## Install

```bash
uv add cuere            # core (pure-Python)
uv add 'cuere[image]'   # + PNG export (pulls in Pillow)
```

cuere needs Python 3.13+. The core depends only on
[segno](https://github.com/heuer/segno), [typer](https://typer.tiangolo.com/),
and [Rich](https://github.com/Textualize/rich).

## Your first QR code

=== "Python"

    ```python
    from cuere import render, show

    show("HELLO")                 # print the code to stdout
    text = render("HELLO")        # or get it back as a str
    ```

=== "CLI"

    ```bash
    cuere "HELLO"                 # render to the terminal
    echo "HELLO" | cuere          # or read the payload from stdin
    ```

`show()` prints; `render()` returns the string so you can put it wherever you
like (a log line, a TUI widget, a file).

## Rendering modes

cuere defaults to compact Unicode **half-blocks**. Two more modes are available
— `block` (two full-width chars per module: chunky but maximally robust) and
`ansi` (half-blocks with theme-proof colors):

=== "Python"

    ```python
    show("HELLO", mode="block")
    show("HELLO", mode="ansi")
    show("HELLO", invert=True)    # flip dark/light for light-on-dark terminals
    ```

=== "CLI"

    ```bash
    cuere "HELLO" --mode block
    cuere "HELLO" --mode ansi
    cuere "HELLO" --invert
    ```

See **[Rendering & scanning](guides/rendering.md)** for how the modes differ,
the error-correction rationale, and how to check a code fits the terminal.

## A wallet URI

cuere builds validated payment-request URIs and can shrink the bech32 ones so
the code stays small:

=== "Python"

    ```python
    from decimal import Decimal
    from cuere import bitcoin_uri, optimize_uri, show

    uri = bitcoin_uri("bc1q...", amount=Decimal("0.01"), label="Tip")
    show(optimize_uri(uri))       # smaller, still scannable
    ```

=== "CLI"

    ```bash
    cuere --optimize-uri "bitcoin:bc1q..."
    ```

There are builders for Lightning (`lightning_uri`) and Ethereum
(`ethereum_uri`, `erc20_transfer_uri`) too — see the
**[Wallet URIs cookbook](cookbook/wallet-uris.md)**.

## With Rich

`cuere.rich.QRCode` is a Rich renderable, so it composes with panels, tables,
and `justify`:

```python
from rich.console import Console
from rich.panel import Panel
from cuere.rich import QRCode

Console().print(Panel(QRCode("bitcoin:BC1Q..."), title="scan to pay"), justify="center")
```

## CLI vs API — which to use

| You want to… | Use |
| --- | --- |
| Show a code in a script or a one-off shell command | the **CLI** (`cuere …`) |
| Embed a code in your own Python program | `render()` / `show()` |
| Lay a code out with panels/tables/centering | `cuere.rich.QRCode` |
| Build & validate a wallet payment URI | `bitcoin_uri()` / `lightning_uri()` / `ethereum_uri()` |
| Export an SVG or PNG file | `save()` / `render_bytes()` |

## Next steps

- **[Rendering & scanning](guides/rendering.md)** — modes, EC level, fit checks, Micro QR.
- **[Terminal colors](colors.md)** — ANSI color customization.
- **[Wallet URIs](cookbook/wallet-uris.md)** and **[Exporting](cookbook/exporting.md)** cookbooks.
- **[API reference](reference/api.md)** — every public symbol.
