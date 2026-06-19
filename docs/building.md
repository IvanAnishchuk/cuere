# Building from source

How to build and install cuere from source, including the prerequisites and the
build backend. It documents the project's build transparency and reproducibility
and complements the [dependency policy](security/dependencies.md)
(OSPS-DO-06.01) behind cuere's [OSPS Baseline conformance](security/osps-baseline.md).
For the contribution workflow and quality bar, see the
[Contributing guide](https://github.com/IvanAnishchuk/cuere/blob/main/CONTRIBUTING.md).

## Prerequisites

- **Python ≥ 3.13** — cuere targets modern Python and uses 3.13+ syntax.
- **[uv](https://docs.astral.sh/uv/)** — the project's package/environment
  manager; it drives the build and dependency resolution.
- **git** — sdists are produced from the committed tree (`meson dist`).

There is **no system C/C++ toolchain requirement**: cuere is pure Python and its
one runtime dependency (segno) is pure Python, so the build does not compile
native code.

## Build backend

cuere builds with **[meson-python](https://meson-python.readthedocs.io/)** (a
PEP 517 backend). A few consequences worth knowing:

- **Meson does not glob.** Every shipped module under `src/cuere/` is listed
  explicitly in `src/cuere/meson.build`; `tests/test_packaging.py` fails if the
  list drifts.
- The **version** is defined once, in the root `meson.build`
  (`project(version:)`); `pyproject.toml` declares it `dynamic`.
- **sdists come from `meson dist`** (a git archive), so only committed files are
  included — commit before building an sdist.

## Editable install (development)

```bash
git clone https://github.com/IvanAnishchuk/cuere.git
cd cuere
uv sync                 # editable (PEP 660) install via meson-python
uv sync --extra image   # optional: add the Pillow-backed PNG export
uv sync --extra docs    # optional: add the documentation toolchain
```

## Building wheels and sdists

```bash
uv build                # builds sdist + wheel into dist/
```

Because the sdist is a git archive, **commit your changes first** or they won't
be in the artifact. After editing any `meson.build`, run
`uv sync --reinstall-package cuere` if the editable install looks stale.

## Verifying a build

```bash
uv run pytest           # full suite, 100% branch coverage enforced
uv run ruff check && uv run mypy src/ tests/ && uv run ty check && uv run basedpyright
```

Released artifacts on PyPI and the GitHub releases page carry sigstore
signatures, PEP 740 attestations, SLSA provenance, and a CycloneDX SBOM — see
[verifying a release](https://github.com/IvanAnishchuk/cuere/blob/main/SECURITY.md#verifying-a-release).
