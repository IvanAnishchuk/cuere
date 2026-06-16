---
icon: lucide/qr-code
---

# cuere

QR codes in your terminal — the way Claude Code CLI draws its remote-connection
codes: Unicode half-blocks, low error correction so the code stays small, a
proper quiet zone. Plus a [Rich](https://github.com/Textualize/rich) renderable
and helpers for crypto-wallet URIs.

<!-- qr: HOME -->
```text { .qr }
                                     
                                     
    █▀▀▀▀▀█  ▀▀█▄█  ▄▄▀ ▄ █▀▀▀▀▀█    
    █ ███ █ ▄▀██ ▄ ▀█ ▀ ▄ █ ███ █    
    █ ▀▀▀ █ ▀▄█ ▀ ▄ █ █▀▀ █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀▄▀ █ █ █ ▀▄█ ▀▀▀▀▀▀▀    
    ▀█▄  █▀█ ▀█ ▀ ▄█▀█▄▄▀▄ ▄█▀▄▄     
    ▄█▄▀ █▀▄█▀▄█▀  █▀▀▄ ▀▄  ▀▄       
    ▀▄ ▄▄▄▀▄▀██ ▄█▀██▄▄ █ ██▄  ▄█    
     ▄█▄▄█▀▄▀▄▀ ▄███▀ ▀▄▀▀ ▄█▀█ ▄    
    ▄   ▀ ▀▄ ▄▀ ▀ ▀▄ ▀ █ ▀▄█▄▀█▄▄    
    █▀  █▄▀▀ ▀▄▄▀▀██  ▀▀▄ ▄ ▀▀  ▀    
    ▀ ▀ ▀▀▀ ██ ▀▄▄ ▄ █▄▀█▀▀▀█▄▀▀▀    
    █▀▀▀▀▀█ █▀▄ ▄█▀▀█ ███ ▀ █▀▀ ▄    
    █ ███ █  ▄▀▀▀▀ █▄ ▄███▀▀▀█▄ █    
    █ ▀▀▀ █ ▄ ▀█▀  ▀▄▀▀▀▀▀██▀██▀▄    
    ▀▀▀▀▀▀▀ ▀▀▀▀     ▀ ▀  ▀▀▀ ▀      
                                     
                                     
```

## Install

```bash
uv add cuere            # core
uv add 'cuere[image]'   # + PNG export (pulls in Pillow)
```

Requires Python 3.13+. The core install is pure-Python and depends only on
[segno](https://github.com/heuer/segno), [typer](https://typer.tiangolo.com/),
and [Rich](https://github.com/Textualize/rich).

## A first code

=== "Python"

    ```python
    from cuere import render, show, fits

    show("HELLO")                                   # print to stdout
    text = render("HELLO", mode="block", invert=True)  # returns a str
    if fits("a long payload..."):                   # fits the terminal?
        show("a long payload...")
    ```

=== "CLI"

    ```bash
    cuere "HELLO"                 # render to the terminal
    cuere "HELLO" --mode ansi     # colored half-blocks
    cuere "HELLO" --output png:qr.png # needs cuere[image]
    ```

!!! tip "Scanning"

    cuere defaults to error-correction level **L** and a 4-module quiet zone so
    the code stays compact on screen. If a renderer's contrast fights your
    terminal theme, try `--invert`, or `--mode ansi` with explicit
    `--dark`/`--light` colors. See **[Terminal colors](colors.md)**.

## Where to go next

- **[Cookbook → Wallet URIs](cookbook/wallet-uris.md)** — render `bitcoin:`,
  `lightning:`, `ethereum:`, and WalletConnect `wc:` payment codes.
- **[Cookbook → Exporting](cookbook/exporting.md)** — save SVG and PNG, or get
  raw bytes.
- **[Guides → Terminal colors](colors.md)** — ANSI color customization and
  scanner-contrast caveats.
- **[Guides → Output formats](output-formats.md)** — text, SVG, and PNG.
- **Wallet URI standards** — the [BIP-21](bip-21.md),
  [Lightning](lightning-uri.md), and [EIP-681](eip-681.md) summaries behind the
  builders.
