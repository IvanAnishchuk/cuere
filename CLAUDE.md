# cuere — notes for agents

Pure-Python library: QR codes rendered in the terminal (Unicode half-blocks,
like Claude Code's remote-control screen). Encoder is segno; renderers are
stdlib-only; CLI is typer; Rich integration in `cuere.rich`.

## Layout

**src-layout:** the importable package is `src/cuere/`, tests are in `tests/`
(golden files in `tests/golden/`). The module install list lives in
`src/cuere/meson.build` — there is no globbing, so every new module must be
added there (see meson-python gotchas below). Performance benchmarks live in
`benchmarks/` (pytest-benchmark); like `scripts/`, that dir is **ruff + `ty`
scope only** — `mypy` (`src/ tests/`) and basedpyright (`include`) don't cover
it, it's outside `testpaths`/coverage, and it never ships in the wheel. Modules
and what they own:

- `matrix.py` — the segno-wrapping encoder and the **only** module that imports
  segno. `QRMatrix` (frozen), `ECLevel`, `coerce`, and the shared
  `Encodable` / `EncodeOptions` encode-option types.
- `render.py` — pure-stdlib glyph and vector renderers. `RenderMode`,
  `render_matrix`, `render_svg`, `render_width` / `render_height`, `coerce_mode`,
  the `Color` type with `resolve_color` / `check_color_mode` (ANSI mode's
  `dark`/`light` colors), and the `ANSI_FG`/`ANSI_BG` / `DEFAULT_SCALE` /
  `SVG_DARK`/`SVG_LIGHT` constants. No terminal interaction.
- `terminal.py` — the high-level API: `render`, `show`, `fits`, and the narrow
  `SupportsWrite` sink protocol. Owns terminal-size and NO_COLOR/tty logic.
- `output.py` — the output-format dispatcher: `OutputFormat`, `render_bytes` /
  `save`, `coerce_format`, the `SupportsWriteBytes` sink, and the PNG renderer.
  The **only** module that imports Pillow (lazily, for the `cuere[image]`
  extra). `UnknownFormatError` / `MissingDependencyError` live in `errors.py`.
- `wallet.py` — crypto-URI helpers: the payment-request builders `bitcoin_uri`
  (BIP-21), `lightning_uri` (BOLT11/LNURL/BOLT12), `ethereum_uri` /
  `erc20_transfer_uri` (EIP-681); the `optimize_uri` QR-alphanumeric optimizer
  with its typed `SchemeCase` / `scheme_case` classifier; and
  `is_qr_alphanumeric`. `WalletURIError` lives in `errors.py`.
- `rich.py` — the Rich renderable `QRCode` (imports `rich`; loads on demand).
- `cli.py` + `__main__.py` — the typer CLI `app` (imports `typer`; on demand).
- `errors.py` — exception hierarchy: `CuereError` and subclasses.
- `__init__.py` — public surface (`__all__`) and `__version__`.

## Commands

```bash
uv sync                          # editable install (meson-python PEP 660)
uv run pytest                    # fail_under = 100, branch coverage
uv run pytest benchmarks/ --benchmark-only --no-cov  # perf benchmarks (not the test suite)
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

## Working on this project

- **Project management runs through the `/solo-pm` skill — invoke it
  automatically, without being asked.** This is a solo / AI-assisted project
  tracked on a GitHub Projects v2 board; `/solo-pm` is the PM manual and the
  default entry point for *any* project-management activity. Invoke it
  proactively — at the start of a session that resumes a board item, and
  whenever you plan, prioritize, estimate, update status, move a board card,
  log token spend, or report on work — rather than improvising a process or
  waiting for the user to request it. The only PM work that skips it is a
  trivial one-line status mention inside other work.
- **Run `/code-review` before every push / PR, and to audit already-merged
  code.** It is the real review gate here. The GitHub review bots are
  unreliable on this repo (Codex/Copilot at usage limits; Gemini being sunset),
  so a green or empty bot check is **not** an approval — don't rely on it.
  `/code-review` is what actually gates a change. CodeRabbit is the live second
  opinion (behavior pinned in `.coderabbit.yaml`). On this **public** repo it
  runs free-for-OSS with an **hourly per-developer rate limit** — **not** out of
  credits, so the "billing tab" line in its rate-limit warning is boilerplate
  that does not apply. When a CodeRabbit check is pass/neutral with no
  walkthrough, read the warning for when the window reopens and wait it out. A
  rate-limited auto-review still marks the commit "seen", so a plain
  `@coderabbitai review` returns a hollow result — force a real pass with
  `@coderabbitai full review`.
- **Merge with a merge commit — never squash or rebase.** `main` is protected
  and squash/rebase are disabled; the only button is merge-commit. Keep PR
  commits as separate signed, DCO-signed (`git commit -s`) commits so they
  survive the merge. Admin bypass for the solo-dev self-review block:
  `gh pr merge <N> --merge --admin`.

## Typing & imports

- **No `from __future__ import annotations`.** It is unnecessary on 3.13 for
  modern syntax, and without it annotations stay honest (evaluated at runtime).
- **Reach for `if TYPE_CHECKING:` only** to break a real import cycle or defer a
  genuinely heavy/optional dependency — never for cheap stdlib/intra-package
  types, which go in plain top-level imports. The `flake8-type-checking` (`TCH`)
  ruff ruleset is intentionally **off**: it forces the opposite and creates churn
  (TYPE_CHECKING blocks → quoted `cast()` types → CodeQL false positives). Don't
  re-enable it or re-introduce the blocks.
- **`import cuere` must not import `rich`, `typer`, or `PIL`/Pillow.** Keep them
  out of `cuere/__init__` and the core modules; `cuere.rich`/`cuere.cli` import
  rich/typer and load only on demand, and `cuere.output` imports Pillow lazily
  inside `_render_png` (the `cuere[image]` PNG extra). The
  `test_importing_cuere_does_not_import_rich_or_typer` and
  `test_importing_cuere_does_not_import_pillow` tests guard this — the deferrals
  that genuinely matter.

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
- Docs pages embed live QR art via `scripts/render_docs_qr.py` (`<!-- qr: KEY
  -->` markers). Its `ART_PAGES` list and the `trailing-whitespace` `exclude:`
  regex in `.pre-commit-config.yaml` must be kept in sync **by hand**: every art
  page needs that exclusion or its significant quiet-zone trailing spaces get
  stripped on commit, silently corrupting the QR art. Today the cookbook is
  excluded as a whole directory (so new recipes are covered automatically) and
  `docs/index.md` by name. `--check` (run in CI via `tests/test_docs_qr.py`)
  catches art *drift*, not a *missing* exclusion — so when adding an art page
  outside the cookbook, update both places.
- `invert` is implemented as `matrix.inverted()` before glyph mapping —
  keep that single code path.
- Error correction defaults to `L` with `boost_error=False`; both are
  deliberate (smaller code on screen) — don't "fix" them.
