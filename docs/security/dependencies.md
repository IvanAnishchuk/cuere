# Dependency management

cuere's dependency policy — how dependencies are selected, obtained, pinned, and
tracked. This is the policy backing OSPS-DO-06.01.

## Philosophy: stdlib-first, minimal

cuere is **standard-library-first**. The renderers, terminal handling, and
wallet-URI helpers are pure stdlib. Third-party code is added only when it earns
its place, and anything that isn't needed for the core path is an **optional
extra** so a plain `import cuere` stays lightweight.

## What cuere depends on

| Dependency | Why | How it ships |
|------------|-----|--------------|
| **segno** | The QR/Micro-QR encoder — the one piece cuere does not reimplement | Required runtime dependency |
| **rich** | The `cuere.rich.QRCode` renderable | Optional; loaded on demand |
| **typer** | The `cuere` CLI | Optional; loaded on demand |
| **Pillow** | PNG export (`cuere[image]`) | Optional extra; imported lazily |

Development tooling (uv, meson-python, pytest, ruff, mypy/ty/basedpyright,
zizmor, gitleaks, and the docs stack) is declared in the project's dev/extras
groups, not in the runtime requirements.

## Selecting a dependency

A new dependency must clear this bar before it is added:

1. **Necessity** — it can't be reasonably covered by the standard library.
2. **License** — compatible with cuere's CC0-1.0 dedication.
3. **Health** — maintained, with a credible security-response track record.
4. **Footprint** — a small, well-scoped transitive tree; prefer pure-Python.
5. **Placement** — if it isn't needed on the core path, it goes in an extra.

## Obtaining and pinning

- Dependencies are resolved and **locked in `uv.lock`** for reproducible installs
  (`uv sync`). The `uv-lock` pre-commit hook keeps the lock in sync with
  `pyproject.toml`.
- CI installs from the lockfile, so builds and audits run against the exact
  pinned set.

## Tracking and auditing

| Tool | Role |
|------|------|
| **OSV-Scanner** | Scans the dependency set for known vulnerabilities in CI |
| **pip-audit** | Supply-chain audit (run by `scripts/audit.py`, locally and in CI) |
| **dependency-review** | Flags risky dependency changes on pull requests |
| **dependabot** | Opens automated update PRs, including security updates |

Updates flow in as dependabot PRs, which pass the full quality gate (tests, type
checks, audits) before merge. Vulnerabilities found in a dependency are tracked
to an upstream fix or a version pin; they are out of scope for cuere's own
[vulnerability reporting](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md)
(report those upstream).
