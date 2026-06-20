# Atheris fuzzing (dev-only)

Coverage-guided ([libFuzzer](https://llvm.org/docs/LibFuzzer.html)-backed)
fuzzing of cuere's renderers and wallet-URI helpers with
[Atheris](https://github.com/google/atheris). This is a **pilot** — see the
keep-or-drop rationale in [`docs/fuzzing.md`](../../docs/fuzzing.md) (issue
[#96](https://github.com/IvanAnishchuk/cuere/issues/96)).

Atheris is **not** installed by the default `uv sync`: it is a heavy native
dependency (it builds against `clang`/libFuzzer) and is intentionally kept out
of the runtime and the blocking CI path. It lives in its own `fuzz` dependency
group (Apache-2.0, so — unlike the proprietary HypoFuzz — it is an allow-listed,
declared dependency).

Atheris publishes manylinux **x86_64** wheels (the locked set); on other
platforms (macOS, Windows, ARM) `uv sync --group fuzz` builds it from source and
needs a working `clang`/libFuzzer toolchain. The pilot is developed and run on
Linux x86_64.

## Layout

- `atheris/harness.py` — shared bootstrap: re-exports `atheris` and provides
  `instrument()` (instrument cuere for coverage feedback) and `run()` (Setup +
  Fuzz), so each target carries no boilerplate.
- `atheris/fuzz_*.py` — one fuzz target each. Plain scripts that wrap their
  `cuere` imports in `instrument()` and end with `run(fuzz_target)`; run
  directly, never imported by the test suite (they would fuzz forever on import).
- `test_atheris_targets.py` — a pytest smoke test that runs each target for a
  few seconds and fails on a crash, or if a target never actually started
  fuzzing. Gated behind the `atheris` marker, so the default `uv run pytest`
  skips it.

## Running

```bash
uv sync --group fuzz                       # install Atheris (needs clang)

# Short smoke run of every target (default 10s each). --no-cov because the
# targets fuzz in subprocesses, so the suite's 100% coverage gate does not apply.
uv run --group fuzz pytest tests/fuzz -m atheris --no-cov
FUZZ_SECONDS=120 uv run --group fuzz pytest tests/fuzz -m atheris --no-cov

# Drive a single target for a real session (Ctrl-C to stop), passing
# libFuzzer flags straight through:
uv run --group fuzz python tests/fuzz/atheris/fuzz_render.py
uv run --group fuzz python tests/fuzz/atheris/fuzz_wallet.py -max_total_time=300
```

A crash writes a `crash-*` reproducer file in the working directory; replay it
with `… python tests/fuzz/atheris/fuzz_render.py crash-<hash>`.
