# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
