# cuere

[![test](https://github.com/IvanAnishchuk/cuere/actions/workflows/test.yml/badge.svg)](https://github.com/IvanAnishchuk/cuere/actions/workflows/test.yml)
[![lint](https://github.com/IvanAnishchuk/cuere/actions/workflows/lint.yml/badge.svg)](https://github.com/IvanAnishchuk/cuere/actions/workflows/lint.yml)
[![typecheck](https://github.com/IvanAnishchuk/cuere/actions/workflows/typecheck.yml/badge.svg)](https://github.com/IvanAnishchuk/cuere/actions/workflows/typecheck.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/IvanAnishchuk/cuere/badge)](https://scorecard.dev/viewer/?uri=github.com/IvanAnishchuk/cuere)

QR codes in your terminal — the way Claude Code CLI draws its remote-connection
codes: Unicode half-blocks, low error correction so the code stays small, a
proper quiet zone. Plus a [Rich](https://github.com/Textualize/rich) renderable
and helpers for crypto-wallet URIs.

```
█▀▀▀▀▀█ ▄▀ ▄▀ █▀▀▀▀▀█
█ ███ █ ▄▀ ▄  █ ███ █
█ ▀▀▀ █ ▄▄█▀█ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀ █▄█ ▀▀▀▀▀▀▀
█▀█▀▀▄▀▀▀▀  █▀ █ █▄█▄
 ▄▄▄▄▄▀▄▀▀█▀ ▀ ▄█▀  ▀
 ▀▀  ▀▀ ██▀█▄█▄ ▀▄▀▄▄
█▀▀▀▀▀█ ▀▄█▄█▄█▀ ▄▀ █
█ ███ █ █ ▄ █  █  █
█ ▀▀▀ █ █ ▄▀ ▀ ▄█ █ ▄
▀▀▀▀▀▀▀ ▀  ▀ ▀  ▀ ▀
```

## Install

```bash
uv add cuere        # or: pip install cuere
```

## Use

```python
from cuere import render, show, fits

payload = "wc:7f6e504b...@2?relay-protocol=irn&symKey=587d..."
show(payload)                                       # prints to stdout
text = render("HELLO", mode="block", invert=True)   # returns a str
if not fits(payload):                               # does it fit the terminal?
    ...
```

With Rich (centering, panels, layouts):

```python
from rich.console import Console
from rich.panel import Panel
from cuere.rich import QRCode

Console().print(Panel(QRCode("bitcoin:BC1Q..."), title="scan to pay"), justify="center")
```

Wallet URIs — `optimize_uri()` uppercases a **fully lowercase** bech32-style
URI so it encodes in QR alphanumeric mode (a smaller code; BIP-173/BIP-21 are
case-insensitive, so this is lossless). Mixed-case URIs, or those with
non-alphanumeric query parts, are returned unchanged:

```python
from cuere import optimize_uri

optimize_uri("bitcoin:bc1q...")  # -> "BITCOIN:BC1Q..."
```

CLI:

```bash
cuere "wc:...your walletconnect uri..."
echo "some payload" | cuere
cuere HELLO --mode ansi --invert --border 2 --error M
```

### Rendering modes

| mode | one module is | width of a v2 code | notes |
|---|---|---|---|
| `half` (default) | ½ character (`▀▄█`) | 33 cols | survives copy-paste; inherits terminal colors |
| `ansi` | ½ character, forced black-on-white | 33 cols | theme-proof; falls back to `half` when piped or `NO_COLOR` is set |
| `block` | 2 characters (`██`) | 66 cols | most font-robust, twice as wide |

### Scanning notes

- On dark terminals the default mode shows an *inverted* code (light modules
  on dark). Modern phone cameras handle this; for a stubborn scanner pass
  `invert=True` / `--invert`, or use `mode="ansi"` for spec-correct polarity.
- Error correction defaults to `L`: screens don't get dirty or torn, and
  lower correction means a smaller code that fits your terminal.
- The quiet zone (4 modules) is part of the output on purpose — don't strip
  the "blank" margins.

## Development

```bash
uv sync                  # editable install via meson-python
uv run pytest            # 100% branch coverage enforced
uv run ruff check && uv run mypy src/ tests/ && uv run ty check && uv run basedpyright
uv run pre-commit install --install-hooks
```

Build-system notes (meson-python):

- Every shipped file must be listed in `src/cuere/meson.build` — meson does
  not glob. `tests/test_packaging.py` fails if the list drifts.
- The version lives only in the root `meson.build`.
- sdists are produced from *committed* files (`meson dist`); commit before
  `uv build`.

## License

[CC0-1.0](LICENSE) — public domain.
