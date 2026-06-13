# cuere — notes for agents

Pure-Python library: QR codes rendered in the terminal (Unicode half-blocks,
like Claude Code's remote-control screen). Encoder is segno; renderers are
stdlib-only; CLI is typer; Rich integration in `cuere.rich`.

## Commands

```bash
uv sync                          # editable install (meson-python PEP 660)
uv run pytest                    # fail_under = 100, branch coverage
uv run ruff check src/ tests/
uv run mypy src/ tests/          # strict
uv run ty check
uv run basedpyright              # recommended mode; zero warnings expected
uv build                         # sdist + wheel via mesonpy
```

All three type checkers must pass with zero errors AND zero warnings — no
`|| true`, no blanket ignores. Coverage is 100%; structure code so branches
are testable instead of adding pragmas.

Mutation testing (mutmut) is **dev-only**, run with the project *uninstalled*
(`uv sync --no-install-project && uv run --no-sync mutmut run`) — the editable
install's import hook otherwise shadows the mutated tree. See
`docs/mutation-testing.md` for the workflow and accepted equivalent mutants.

## Typing & imports

- **No `from __future__ import annotations`.** It is unnecessary on 3.13 for
  modern syntax, and without it annotations stay honest (evaluated at runtime).
- **Reach for `if TYPE_CHECKING:` only** to break a real import cycle or defer a
  genuinely heavy/optional dependency — never for cheap stdlib/intra-package
  types, which go in plain top-level imports. The `flake8-type-checking` (`TCH`)
  ruff ruleset is intentionally **off**: it forces the opposite and creates churn
  (TYPE_CHECKING blocks → quoted `cast()` types → CodeQL false positives). Don't
  re-enable it or re-introduce the blocks.
- **`import cuere` must not import `rich` or `typer`.** Keep them out of
  `cuere/__init__` and the core modules; `cuere.rich`/`cuere.cli` import them and
  load only on demand. `test_importing_cuere_does_not_import_rich_or_typer`
  guards this — it is the one deferral that genuinely matters.

## meson-python gotchas

- **No globbing.** Every new file under `src/cuere/` must be added to
  `src/cuere/meson.build` (`py.install_sources`), or it silently won't ship
  in wheels. `tests/test_packaging.py` guards this.
- **Version** is defined once, in the root `meson.build` `project(version:)`;
  pyproject has `dynamic = ["version"]`. Never add a static version to
  pyproject (mesonpy errors on the conflict).
- **sdists come from `meson dist`** (git archive): only committed files are
  included, and building an sdist requires a git checkout. Commit before
  `uv build`.
- After editing meson.build, `uv sync --reinstall-package cuere` if the
  editable install looks stale.
- Don't add default-built custom targets to meson.build: `meson compile`
  runs inside every wheel build (including `pip install` from sdist).

## Renderer contract

- Golden files in `tests/golden/` pin the exact output format. If a renderer
  change alters them, regenerate AND scan the new half/ansi goldens with a
  phone camera before committing.
- HALF glyph map: `(top,bottom)` → `' '`/`'▀'`/`'▄'`/`'█'`; dark module =
  foreground ink. Odd-height matrices pad a virtual light bottom row.
- Quiet zone is rendered as real spaces (full-width lines, no rstrip) — a
  scanner needs it in the code's own background.
- `invert` is implemented as `matrix.inverted()` before glyph mapping —
  keep that single code path.
- Error correction defaults to `L` with `boost_error=False`; both are
  deliberate (smaller code on screen) — don't "fix" them.
