# Benchmarks

Performance benchmarks for cuere's encode and render paths, built on
[pytest-benchmark](https://pytest-benchmark.readthedocs.io/). They track how long
encoding and each render mode take so a regression can be caught and attributed.

These are **not** part of the test suite. `pyproject.toml` sets
`testpaths = ["tests"]`, so a bare `uv run pytest` never collects this directory —
the 100%-branch-coverage suite and normal CI are untouched. A dedicated,
informational CI job (`.github/workflows/benchmark.yml`) runs them on every push
and pull request and uploads the timings as a JSON artifact.

## Running locally

```bash
uv run pytest benchmarks/ --benchmark-only --no-cov
```

`--no-cov` disables the coverage instrumentation that `addopts` would otherwise
inject (tracing skews timings). The output is grouped into `encode`, `render`,
and `high-level` sections.

## Comparing runs / catching regressions

Save a baseline and compare later runs against it:

```bash
# Save a named baseline under .benchmarks/
uv run pytest benchmarks/ --benchmark-only --no-cov --benchmark-autosave

# After a change, compare against the most recent saved run
uv run pytest benchmarks/ --benchmark-only --no-cov --benchmark-compare

# Or compare two saved runs directly
uv run pytest-benchmark compare
```

The CI job records `--benchmark-json` output as the `benchmark-results` artifact,
so historical timings are available per run.

## Future: a regression gate

The suite is the foundation for an enforced threshold (the issue tracks this as a
"later" step). pytest-benchmark can fail a run when a metric regresses past a
margin, e.g.:

```bash
uv run pytest benchmarks/ --benchmark-only --no-cov \
  --benchmark-compare --benchmark-compare-fail=mean:10%
```

Until a stable baseline and a noise-tolerant margin are chosen, the CI job stays
informational (it records timings but never fails on them).
