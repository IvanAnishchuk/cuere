# Copilot instructions for cuere

`cuere` renders QR codes in the terminal (Unicode half-blocks, low error
correction, a real quiet zone) — a pure-Python library built on `segno`, with
a typer CLI and a Rich renderable, for crypto-wallet CLIs and similar tools.

## Project conventions

- Python `>=3.13`, `src/` layout, `py.typed`, license CC0-1.0.
- uv-native; build backend is **meson-python** (meson does not glob — every
  shipped file must be listed in `src/cuere/meson.build`; the version lives
  only in the root `meson.build`).
- `segno` is imported only in `src/cuere/matrix.py`; `src/cuere/render.py` is
  pure stdlib and deterministic.
- Imports go at the top of the file. Core dependencies are limited to
  `segno`, `typer`, and `rich`.

## Quality bar (do not weaken in suggestions)

- `pytest` enforces **100% branch coverage** (`fail_under=100`).
- `ruff`, `mypy --strict`, `ty`, and `basedpyright` (recommended mode) must
  all pass with **zero errors and zero warnings** — never suggest blanket
  `# type: ignore`, `# noqa`, or `|| true` to silence a real issue.

## What to focus reviews on

- **Renderer correctness** in `render.py`/`matrix.py`: half-block glyph
  mapping, odd-height bottom-row padding, and the quiet zone rendered as real
  spaces. `tests/golden/*.txt` pin exact output — flag changes that alter them
  without regenerating and re-scanning the codes.
- **Intentional choices — do not flag as bugs:** error-correction level `L`
  and `boost_error=False`; the ≥4-module quiet zone (never `rstrip` it);
  `invert` via `matrix.inverted()`; `NO_COLOR` as presence-based.
- **Security:** treat payloads (wallet URIs, secrets) as sensitive — never log
  them; keep the gitleaks allowlist path-scoped (not a global regex); keep
  workflow permissions least-privilege.

Prefer a few high-confidence, high-severity findings over many style nits that
ruff and the formatter already cover.
