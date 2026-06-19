# Architecture & design

This page describes cuere's components, the actors that interact with it, and
the data flow and trust boundaries between them. It is the design documentation
backing OSPS-SA-01.01 and the companion to the
[threat model](threat-model.md).

## What cuere is

cuere is a **pure-Python library** (plus a thin CLI) that turns a payload into a
QR code rendered for a terminal — Unicode half-blocks by default — or exported to
SVG/PNG. It performs **no network I/O at runtime** and executes none of its
input: a payload is *data* that gets encoded into a QR matrix, never code that
runs.

## Actors

| Actor | Role | Boundary |
|-------|------|----------|
| **Calling application / user** | Supplies the payload and options through the Python API or the `cuere` CLI | Untrusted input crosses into the library |
| **Terminal / output sink** | Receives rendered text, or a file/bytes sink receives SVG/PNG | cuere writes here |
| **segno** | The QR/Micro-QR encoder (the only runtime dependency) | Trusted, pinned dependency |
| **Optional extras** | `rich` (renderable), `typer` (CLI), `Pillow` (PNG) — loaded on demand | Trusted, pinned, optional |
| **Build & release pipeline** | GitHub Actions builds, signs, and publishes releases | Trusted CI, see the threat model |
| **PyPI** | Distribution channel for released wheels/sdists | Trusted distribution point |

## Components

The package is split so that the core import stays light (no `rich`, `typer`, or
`Pillow` pulled in by `import cuere`):

| Module | Owns |
|--------|------|
| `matrix` | The segno-wrapping encoder (`QRMatrix`, `ECLevel`); the **only** module that imports segno |
| `render` | Pure-stdlib glyph and SVG renderers; the `Color` model and ANSI/SVG constants — no terminal interaction |
| `terminal` | The high-level API (`render`, `show`, `fits`); terminal-size and `NO_COLOR`/tty logic |
| `output` | Output-format dispatch (`render_bytes`, `save`); the **only** module that imports Pillow (lazily, for the `cuere[image]` PNG extra) |
| `wallet` | Crypto-URI builders (BIP-21, BOLT11/LNURL/BOLT12, EIP-681) and the QR-alphanumeric `optimize_uri` |
| `rich` | The Rich renderable `QRCode` (imports `rich`; on demand) |
| `cli` / `__main__` | The typer CLI (imports `typer`; on demand) |
| `errors` | The `CuereError` exception hierarchy |

## Data flow

```text
payload (str/bytes) ──► matrix.encode ──► QRMatrix (frozen, immutable)
   (CLI/API input)        (via segno)         │
                                              ├─► render_matrix ──► terminal glyphs ──► stdout / str
                                              ├─► render_svg     ──► SVG text        ──► file / bytes
                                              └─► render_bytes   ──► PNG (Pillow)     ──► file / bytes
```

1. A payload and options enter through `terminal.render`/`show`/`fits`, the
   `cuere.rich.QRCode` renderable, or the `cuere` CLI.
2. `matrix.encode` hands the payload to segno and wraps the result in a frozen
   `QRMatrix` (an immutable grid of booleans).
3. A renderer maps the matrix to terminal glyphs, an SVG, or — through the
   optional Pillow path — a PNG.
4. The result is returned as a string/bytes, or written to a sink (stdout, a
   file, or a caller-provided writer).

## Trust boundaries

- **Input is data, not code.** The payload is encoded into the QR matrix; cuere
  never `eval`s, imports, or executes it.
- **The terminal boundary is explicit.** Only the renderers emit characters to a
  terminal. In `half`/`block` modes the output is QR glyphs and spaces. In `ansi`
  mode the only escape sequences are SGR colour codes **derived from the validated
  `dark`/`light` colour options** — never from the payload — so a crafted payload
  cannot inject terminal escape sequences. See the
  [threat model](threat-model.md) for the analysis.
- **No ambient authority.** At runtime cuere opens no network connections and
  reads no files except when the CLI is explicitly given `--input <file>`.
- **Optional dependencies stay optional.** `rich`, `typer`, and `Pillow` are
  imported lazily so the attack surface of a plain `import cuere` is just the
  standard library plus segno.
