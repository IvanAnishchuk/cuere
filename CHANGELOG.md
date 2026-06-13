# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
