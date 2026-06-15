# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- File and bytes export beyond the terminal. `render_bytes()` returns the
  encoded `bytes` for a named `OutputFormat`, and `save()` writes them to a path
  or binary stream — inferring the format from a `.txt` / `.svg` / `.png` suffix
  when one is not given. Three formats ship: `text` (the terminal glyph
  rendering, honoring `mode` / `invert`), `svg` (a standalone vector document,
  also exposed directly as `render_svg()`), and `png` (a raster image that needs
  the optional `cuere[image]` extra — Pillow, imported lazily so `import cuere`
  never pulls it in). `scale` sets pixels-per-module for `svg` / `png`. Unknown
  formats raise `UnknownFormatError`; a missing optional dependency raises
  `MissingDependencyError` (both `CuereError`s). The CLI gains
  `--output FORMAT[:PATH]` (PATH `-` or omitted means stdout; the default stays
  terminal output) and `--scale`. Also adds the `SupportsWriteBytes` sink
  protocol. Documented in a new `docs/output-formats.md` and the cookbook.
  Closes #23, #24, #25.
- `lightning_uri()` — a typed `lightning:` URI builder for bech32 Lightning
  payloads (BOLT11 invoices `lnbc…`, LNURL `lnurl1…`, BOLT12 offers `lno1…`).
  The payload is validated structurally (a single-case run of ASCII
  alphanumerics beginning `ln`) without a checksum verify, mirroring
  `bitcoin_uri`; invalid input raises `WalletURIError`. A lowercase result
  composes with `optimize_uri` for a smaller QR. Documented in
  `docs/cookbook.md` and a new `docs/lightning-uri.md`.
- `SchemeCase` and `scheme_case()` — a public, typed classifier for how
  `optimize_uri` treats a URI's scheme: `INSENSITIVE` (bech32 — `bitcoin:` /
  `lightning:` — may be uppercased), `SIGNIFICANT` (case carries meaning —
  `ethereum:` EIP-55, `wc:` WalletConnect — never folded), or `UNKNOWN`
  (unrecognized scheme, also never folded). `optimize_uri` now gates on this, so
  `wc:` is recognized **explicitly** as case-significant rather than incidentally
  passed through.
- `ethereum_uri()` and `erc20_transfer_uri()` — typed
  [EIP-681](https://eips.ethereum.org/EIPS/eip-681) `ethereum:` request builders.
  `ethereum_uri(address, *, value=None, chain_id=None, gas_limit=None,
  gas_price=None)` builds a native payment (`value` in **wei**, matching the
  spec); `erc20_transfer_uri(token, *, to, amount, ...)` builds the ERC-20
  `transfer(address,uint256)` form (`amount` in the token's base units).
  Addresses are validated structurally as `0x` + 40 hex digits with their
  EIP-55 checksum case preserved (so these URIs must never go through
  `optimize_uri`); numeric arguments are positive `uint256` integers. Invalid
  input raises `WalletURIError`. Documented in `docs/cookbook.md`.
- `docs/bip-21.md` and `docs/eip-681.md` — condensed summaries of the wallet-URI
  standards cuere implements (BIP-21/BIP-173 for `bitcoin_uri`; EIP-681/EIP-55/
  EIP-155 and ERC-20 `transfer` for the ethereum builders).
- `bitcoin_uri()` — a typed BIP-21 `bitcoin:` payment-request builder
  (`bitcoin_uri(address, *, amount=None, label=None, message=None)`). It
  validates the address alphabet, renders `amount` as a plain BTC decimal
  (`Decimal`/`int`/`str`; positive, finite, satoshi precision — never `float`),
  and percent-encodes `label`/`message`. Returns a plain `str` that composes
  with `optimize_uri` and `render`/`show`. Invalid input raises the new
  `WalletURIError` (a `CuereError`). Documented in a new `docs/cookbook.md`.
- Mutation testing with `mutmut` (dev dependency, run locally — not in CI),
  configured in `pyproject.toml` and documented in `docs/mutation-testing.md`,
  with the set of accepted equivalent mutants recorded there. Includes a mypy
  type-check pass (`mutmut-mypy.ini`) that catches type-error mutants without a
  runtime test, and a no-shrink hypothesis profile for deterministic runs.
- Behavioral regression tests closing the gaps mutation testing surfaced:
  exact error/warning messages (`WidthError`, invalid render mode), encode-option
  pass-through in `render`/`fits`/`rich.QRCode`, block-mode width/height in
  `fits`/`show`/`QRCode.__rich_measure__`, the `show` exact-fit boundary,
  per-row Rich segments, and first-colon URI scheme parsing in `optimize_uri`.
- `tests/test_types.py`: `assert_type` regression tests pinning the inferred
  types of the public API.
- `zizmor` GitHub Actions security audit: dev dependency, a local pre-commit
  hook (offline), and a CI workflow running online audits with SARIF upload to
  code scanning.
- `.github/settings.yml` (repository-settings app): `security_and_analysis`
  (secret scanning + push protection + Dependabot security updates), branch
  protection on `main`, and the PyPI/TestPyPI environments — as code.
- `.github/CODEOWNERS`.
- gitleaks now uploads its SARIF to code scanning.
- `.coderabbit.yaml` — the CodeRabbit review configuration, pinned in-repo
  rather than left to dashboard defaults: assertive profile, auto-review on pull
  requests targeting `main`, path filters that skip generated files (`uv.lock`,
  build output, golden fixtures), and house-style review instructions.
  CodeRabbit's bundled `ruff` and `gitleaks` are disabled there since CI already
  enforces both. CodeRabbit remains a best-effort second opinion; `/code-review`
  and CI are the gate.
- `.well-known/security.txt` (RFC 9116) — machine-readable security contact.
- Contributor governance: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue
  templates (bug / feature / question) and a pull-request template.
- `SupportsWrite` — a narrow text-sink protocol (any object with `write(str)`),
  exported from `cuere`. It is what `show(out=...)` now accepts.
- Test-hardening pass: edge-case and property coverage for empty/whitespace
  payloads, near-maximal payloads, all four EC levels (encoding + monotonic
  version growth), the reachable Micro QR variants (M2–M4, plus the M1-skip and
  the rejected `H`/oversized cases), extreme borders, that pure `render()`
  keeps ANSI color regardless of `NO_COLOR`, and round-trip strategies that
  exercise the renderers against real encoder output (not only synthetic bit
  patterns).

### Changed

- `optimize_uri()` is refactored onto the new `scheme_case()`; its behavior is
  unchanged (case-insensitive, lowercase, no-query URIs are uppercased;
  everything else is returned verbatim), but `ethereum:` and `wc:` are now
  deliberately classified as case-significant rather than relying on the
  unknown-scheme default.
- Dropped `from __future__ import annotations` and the `if TYPE_CHECKING:`
  gating of cheap stdlib/intra-package imports — those are now plain runtime
  imports. Removed the `flake8-type-checking` (`TCH`) ruff ruleset, which had
  been mechanically forcing both patterns plus quoted `typing.cast` types. The
  lazy import of `rich`/`typer` is unaffected (still enforced by `cuere/__init__`
  not importing them, guarded by a test).
- DRY'd the encode options across the high-level API: `render`/`fits`/`show`/
  `rich.QRCode`/`coerce` now take `**options: Unpack[EncodeOptions]` (one
  `EncodeOptions` TypedDict) plus a shared `Encodable` type alias, so the option
  set and its defaults live once in `QRMatrix.encode`. Calls like
  `render(data, border=2, error="H")` are unchanged. Also centralized the ANSI
  color values shared by `render` and `rich`.
- `show(out=...)` is typed as the narrow `SupportsWrite` protocol instead of
  `typing.IO[str]`, matching what it actually needs (a single `write`; `isatty`
  is probed defensively). Backward compatible — every `IO[str]` already
  satisfies it — and it removes the double-`cast` workaround the tests needed to
  pass a write-only stream.
- mypy: made `strict_equality` and `warn_redundant_casts` explicit in the
  config (both already implied by `strict = true`).

### Fixed

- The CLI now reports a clean `error: …` (exit 1) instead of an uncaught
  traceback when `--input` or stdin holds non-UTF-8 bytes (`UnicodeDecodeError`
  is a `ValueError`, so it previously slipped past the `(CuereError, OSError)`
  handler).
- Corrected mismatched action version comments (e.g. `setup-uv` was labelled
  `v4.2.0` but pinned to `v8.2.0`; CodeQL `v3.27.5`→`v4.36.2`; gitleaks
  `v2.3.6`→`v3.0.0`). The pinned SHAs are unchanged; the comments now match.

### Security

- Hardened the release build against cache poisoning (`enable-cache: false`
  on the publish build's `setup-uv`).

## [0.1.0] - 2026-06-13

### Added

- `QRMatrix` encoding layer over segno (error level `L` by default, no
  error-boost, quiet zone baked in); its `.modules` grid is the public
  raw-matrix accessor.
- Renderers: `half` (Claude-Code-style Unicode half-blocks), `block`
  (double-width full blocks), `ansi` (forced black-on-white colors).
- High-level `render()` / `show()` / `fits()` with optional Micro QR and
  error-boost, terminal width/height fit checks, and `NO_COLOR`/tty-aware
  ANSI fallback.
- Rich renderable `cuere.rich.QRCode` with exact measurement.
- `optimize_uri()` — lossless uppercase optimization for fully-lowercase
  `bitcoin:`/`lightning:` (bech32) wallet URIs to reach QR alphanumeric mode.
- typer CLI: `cuere [DATA | --input FILE]` with `--mode`, `--invert`,
  `--border`, `--error`, `--micro`, `--boost-error`, `--optimize-uri`,
  `--check-width/--no-check-width`, `--force`.
- `AGENTS.md` and `.github/copilot-instructions.md` with project conventions
  and review guidelines for AI review agents (Codex, GitHub Copilot).

### Changed

- `NO_COLOR` disables ANSI output whenever the variable is present, regardless
  of its value (including empty), per the no-color.org spec.
- The CLI strips only trailing newlines from stdin (`rstrip("\r\n")`),
  preserving intentional payload whitespace.
- The release SBOM excludes dev dependencies (`uv export --no-dev`).

### Fixed

- An invalid `border` or render `mode` raises `CuereError` rather than leaking
  a bare `ValueError`, keeping the public exception contract consistent.

### Security

- OSV-Scanner findings fail CI; the coverage-comment `workflow_run` job is
  restricted to same-repository pull-request runs; the gitleaks allowlist is
  scoped to a single test file; `scripts/audit.py` subprocesses have a timeout.
- Release publish routing uses anchored version matching (not substring) to
  choose PyPI vs TestPyPI, so it cannot misroute on incidental tag/branch text.
- Release builds publish via PyPI trusted publishing (OIDC) with sigstore
  signatures, SLSA provenance, PEP 740 attestations, and a CycloneDX SBOM.

[Unreleased]: https://github.com/IvanAnishchuk/cuere/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/IvanAnishchuk/cuere/releases/tag/v0.1.0
