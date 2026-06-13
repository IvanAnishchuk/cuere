# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `AGENTS.md` and `.github/copilot-instructions.md` with project conventions
  and review guidelines for AI review agents (Codex, GitHub Copilot).

### Changed

- `NO_COLOR` now disables ANSI output whenever the variable is present,
  regardless of its value (including empty), per the no-color.org spec.
- The CLI strips only trailing newlines from stdin (`rstrip("\r\n")`) instead
  of all surrounding whitespace, preserving intentional payload whitespace.
- The release SBOM now excludes dev dependencies (`uv export --no-dev`), so it
  describes only the published package's runtime dependencies.
- Renamed `LICENSE` to `LICENSE.md`.

### Fixed

- `QRMatrix.encode` wraps an invalid `border` (e.g. negative) in
  `EncodingError` instead of leaking segno's `ValueError`.
- Corrected the README usage example (undefined `payload`) and narrowed the
  `optimize_uri()` description to its actual contract.
- Set a valid author email in project metadata (an empty `email` is invalid
  per the PEP 621 specification).
- The `coverage-comment` workflow now requests `actions: read` so it can
  download the triggering Test run's artifacts.

### Security

- OSV-Scanner findings now fail CI (removed `continue-on-error`).
- The coverage-comment `workflow_run` job is restricted to same-repository
  runs so fork PRs cannot reach it with write permissions.
- Scoped the gitleaks allowlist to the single test file holding the
  fabricated wallet-URI vector, so it cannot mask secrets elsewhere
  (verified: a same-shape secret outside that file is still flagged).
- `scripts/audit.py` subprocess calls now have a timeout so a hung tool
  cannot stall CI or pre-push indefinitely.

## [0.1.0] - 2026-06-13

### Added

- `QRMatrix` encoding layer over segno (error level `L` by default, no
  error-boost, quiet zone baked in).
- Renderers: `half` (Claude-Code-style Unicode half-blocks), `block`
  (double-width full blocks), `ansi` (forced black-on-white colors).
- High-level `render()` / `show()` / `fits()` with terminal-width checking
  and `NO_COLOR`/tty-aware ANSI fallback.
- Rich renderable `cuere.rich.QRCode` with exact measurement.
- `optimize_uri()` — lossless uppercase optimization for bech32-style wallet
  URIs (QR alphanumeric mode).
- typer CLI: `cuere [DATA]` with `--mode`, `--invert`, `--border`,
  `--error`, `--optimize-uri`, `--check-width/--no-check-width`, `--force`.

[Unreleased]: https://github.com/IvanAnishchuk/cuere/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/IvanAnishchuk/cuere/releases/tag/v0.1.0
