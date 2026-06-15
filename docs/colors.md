# Terminal colors

cuere's `ansi` render mode draws a QR code with explicit SGR colors instead of
inheriting the terminal's theme. By default that is spec-correct black modules on
a white ground; `dark` and `light` let you choose your own.

```python
from cuere import show

show("HELLO", mode="ansi")                                   # default: black on white
show("HELLO", mode="ansi", dark="#1a1a1a", light="#fafafa")  # soft truecolor
show("HELLO", mode="ansi", dark="green")                     # green modules, white ground
```

## Where colors apply

Color is a property of **`ansi` mode only** — it is the mode that emits SGR
codes. The `half` and `block` modes draw plain glyphs that inherit the
terminal's own foreground/background, so they have nothing to color. Passing
`dark` / `light` to them raises `ColorError` rather than silently doing nothing:

```python
render("HELLO", mode="half", dark="red")   # ColorError: dark/light colors require mode 'ansi'
```

The two colors thread through the whole API identically:

| Surface | how |
|---|---|
| `render(data, mode="ansi", dark=…, light=…)` | returns the colored string |
| `show(data, mode="ansi", dark=…, light=…)` | writes it (subject to the `NO_COLOR` guard below) |
| `cuere … --mode ansi --dark … --light …` | the CLI (the flags need `--mode ansi`) |
| `cuere.rich.QRCode(data, mode="ansi", dark=…, light=…)` | the Rich renderable |

## Specifying a color

`dark` (the modules) and `light` (the ground) each take a `Color`:

| form | example | meaning |
|---|---|---|
| name | `"red"`, `"bright_blue"`, `"Bright Red"` | one of the 16 standard ANSI colors (case- and separator-insensitive) |
| palette index | `16`, `"231"` | an xterm 256-color index `0-255` (an `int`, or its string form) |
| hex truecolor | `"#ff8800"`, `"#f80"` | a 24-bit `#rrggbb` / `#rgb` color |
| rgb truecolor | `(255, 136, 0)`, `"255,136,0"` | a 24-bit `(r, g, b)` triple, or its `"r,g,b"` string |

Anything else raises `ColorError`. Either argument may be omitted to keep its
default — palette `16` (true black) for `dark`, `231` (true white) for `light`.

### Named colors are theme-dependent

The 16 names map to palette indices `0-15`, which are exactly the slots a
terminal theme is free to remap: a "black" may render as dark grey, a "white" as
off-white. The **defaults deliberately avoid this** — palette `16` and `231` are
fixed points in the 6x6x6 color cube, true black and true white on every
terminal. For a guaranteed appearance, prefer an index of `16` or higher, or a
truecolor value, over a name.

## `NO_COLOR` and non-terminals

`render()` always emits exactly the SGR you ask for — it is the pure string
builder. `show()` is the polite one: when
[`NO_COLOR`](https://no-color.org/) is set, or the stream is not a TTY, it falls
back from `ansi` to plain `half` glyphs, and your `dark` / `light` fall back with
it (a no-color context should get no color at all). Pass `force=True` (CLI
`--force`) to emit the colors regardless.

## Scanner-contrast caveat

A scanner locates a code by the **contrast between dark and light modules**, not
by hue — so a pretty color scheme can quietly become an unscannable one:

- **Keep strong light/dark contrast.** Low-contrast pairs (two mid-greys, or
  `dark="blue"` on `light="black"`) can stop a code decoding even when it looks
  fine to you. When in doubt, the black-on-white default is the safe choice.
- **Polarity matters.** Scanners expect dark modules on a lighter ground. An
  inverted scheme (light on dark) reads on many modern phone cameras but not all;
  if you want light-on-dark, prefer `invert=True` over hand-rolling it with
  colors, and test with a real scanner.
- **Hue is cosmetic, not magic.** Red-on-white scans about as well as
  black-on-white; yellow-on-white often will not (too little luminance contrast).
  Treat color as decoration over a high-contrast base, and always scan a code you
  intend other people to use.

See also [output formats](output-formats.md) for SVG/PNG export — those use their
own fixed black/white and are unaffected by `dark` / `light`.
