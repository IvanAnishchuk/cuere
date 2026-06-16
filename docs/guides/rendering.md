---
icon: lucide/scan-line
---

# Rendering & scanning

How cuere turns a payload into terminal pixels, and how to keep the result
scannable. For the wallet-URI recipes see the
[cookbook](../cookbook/wallet-uris.md); for color customization see
[Terminal colors](../colors.md).

## Rendering modes

A QR matrix is a grid of dark/light modules. cuere has three ways to draw it,
chosen with `mode=` (Python) or `--mode` (CLI):

| Mode | Glyphs | Size | When |
| --- | --- | --- | --- |
| `half` *(default)* | Unicode half-blocks (`▀ ▄ █`), two modules per character row | 1 cell wide, ½ cell tall per module | the compact default — what Claude Code's remote-control screen uses |
| `block` | two full-width chars per module (`██`) | **2×** as wide | maximum glyph robustness; fonts that render half-blocks poorly |
| `ansi` | half-blocks with forced SGR colors | same as `half` | a **theme-proof** code: explicit black-on-white so a dark/solarized terminal can't invert your contrast |

```python
from cuere import show

show("HELLO")                 # half
show("HELLO", mode="block")
show("HELLO", mode="ansi")
```

`ansi` mode emits raw color codes, so `show()` quietly falls back to `half`
when output is not a TTY or `NO_COLOR` is set (pass `force=True` to override).
Customizing the ANSI colors is covered in [Terminal colors](../colors.md).

## Inversion

`invert=True` (`--invert`) swaps dark and light modules. The dark module is the
ink, so on a light-on-dark terminal an inverted code often reads better:

```python
show("HELLO", invert=True)
```

Inversion is a single code path (`QRMatrix.inverted()`) shared by every
renderer, so it behaves identically for text, SVG, and PNG.

## Error correction, and why L is the default

QR error correction lets a damaged code still decode, at the cost of more
modules (a bigger code). The levels are `L` (~7%), `M` (~15%), `Q` (~25%),
`H` (~30%).

cuere defaults to **`L`** — the *lowest* — on purpose: a code on a screen isn't
subject to smudges, tears, or print noise, so the redundancy buys nothing and
just makes the code larger and harder to fit a terminal. Raise it only if you
expect real-world damage (e.g. the code will be photographed off a screen at an
angle, or printed):

```python
from cuere import ECLevel, show

show("HELLO", error=ECLevel.Q)   # or error="Q"
```

`boost_error` is off by default too: segno would otherwise silently raise the
level whenever there's spare capacity, growing the module count for no benefit
on screen. Turn it on with `boost_error=True` (`--boost-error`) if you do want
the free upgrade.

## Quiet zone

The **quiet zone** is the light margin a scanner needs around the code. cuere
renders it as real background (spaces / light modules), full-width, never
stripped — a scanner needs the margin in the *code's own* background, not
whatever the terminal happens to show behind it. It defaults to 4 modules (the
spec minimum); change it with `border=` / `--border`.

## Does it fit the terminal?

Width is the hard constraint: if a code wraps, it will not scan. `fits()` checks
both width and height against the current terminal size:

```python
from cuere import fits, show

if fits("a long payload"):
    show("a long payload")
```

`show()` itself does a **width-only** check and raises
[`WidthError`](../reference/api.md#cuere.errors.WidthError) by default when the
code is too wide (a too-*tall* code merely scrolls and stays scannable). Soften
that with `on_too_wide`:

```python
show(payload, on_too_wide="warn")     # warn instead of raise
show(payload, on_too_wide="render")   # render anyway
```

For your own layout maths, `render_width()` / `render_height()` give the
terminal footprint (in columns / rows) for a matrix and mode.

## Micro QR

`micro=True` (`--micro`) produces a **Micro QR** code — smaller, for small
payloads only. Micro codes carry less data and support fewer error-correction
levels; an oversized payload or an unsupported level raises
[`EncodingError`](../reference/api.md#cuere.errors.EncodingError):

```python
show("123", micro=True)
```

## Scanning tips

- **Contrast is everything.** If a code won't scan, the usual cause is your
  terminal theme inverting or tinting the blocks. Try `--invert`, or
  `--mode ansi` (which forces black-on-white regardless of theme).
- **Zoom out** so the whole code — including the quiet zone — is visible without
  scrolling; `fits()` tells you whether it will be.
- **Phone cameras** read screens fine at `L`; you rarely need a higher level.
- Regenerate goldens and **scan them with a real phone** after any renderer
  change (the project pins exact output in `tests/golden/`).
