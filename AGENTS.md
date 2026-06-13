# AGENTS.md

Guidance for AI coding/review agents (Codex, etc.) working in this repo.
Humans: see `README.md`; Claude Code: see `CLAUDE.md` (more detailed).

## What this is

`cuere` renders QR codes in the terminal the way Claude Code's CLI draws its
remote-connection codes (Unicode half-blocks, low error correction, a real
quiet zone). Pure-Python, built on `segno`, with a typer CLI and a Rich
renderable. Intended as a reusable building block for crypto-wallet CLIs.

## Setup & checks

```bash
uv sync                       # editable install (meson-python)
uv run pytest                 # 100% BRANCH coverage is enforced (fail_under=100)
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/
uv run mypy src/ tests/       # strict
uv run ty check
uv run basedpyright           # recommended mode — zero warnings expected
uv build                      # sdist + wheel
```

All three type checkers must pass with **zero errors and zero warnings**. No
`# type: ignore`/`# noqa`/`|| true` to paper over a real problem. Imports go
at the top of the file.

## Conventions

- `src/` layout, `py.typed`, `requires-python >=3.13`, license CC0-1.0.
- Build backend is **meson-python**: meson does not glob, so every shipped
  file must be listed in `src/cuere/meson.build`. `tests/test_packaging.py`
  guards this. The version lives only in the root `meson.build`.
- Encoder access (`segno`) is isolated to `src/cuere/matrix.py`; renderers in
  `src/cuere/render.py` are pure stdlib and deterministic.

## Review guidelines

Focus on correctness and security; skip style nits already enforced by ruff
and the formatter. Flag, in priority order:

- **Renderer correctness** (`render.py`, `matrix.py`): the half-block glyph
  mapping, odd-height bottom-row padding, and rendering the quiet zone as real
  spaces are load-bearing. `tests/golden/*.txt` pin the exact output — any
  change that alters them must regenerate the goldens AND be re-scanned with a
  phone; call out changes that don't.
- **Deliberate choices — do NOT "fix" these:** error-correction level `L` and
  `boost_error=False` (smaller code on a screen, which has no damage risk); the
  ≥4-module quiet zone rendered as spaces (never `rstrip` it); `invert`
  implemented as `matrix.inverted()` before glyph mapping (keep the single code
  path); `NO_COLOR` treated as presence-based per the no-color.org spec.
- **Security:** payloads are user data (wallet URIs, secrets) — never log them.
  The gitleaks allowlist is intentionally scoped by path to one test file; do
  not broaden it to a global regex. Keep workflow permissions least-privilege
  and `workflow_run` jobs restricted to same-repo runs.
- **Invariants:** don't weaken the 100% branch-coverage gate or the
  three-type-checker requirement; don't add a dependency to the zero-dep-ish
  core (`segno` + `typer` + `rich` only) without strong reason.
- **Packaging:** a new `src/cuere/*.py` file that isn't added to
  `src/cuere/meson.build` will silently vanish from wheels — flag it.

Apply the closest guidance to the files changed. Prefer a few high-confidence,
high-severity findings over many low-value ones.
