# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
- `.well-known/security.txt` (RFC 9116) — machine-readable security contact.
- Contributor governance: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue
  templates (bug / feature / question) and a pull-request template.

### Fixed

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
