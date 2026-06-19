# Fuzzing with HypoFuzz

cuere's invariants are pinned by [Hypothesis](https://hypothesis.readthedocs.io/)
property tests — the renderer round-trips in `tests/test_render_properties.py`
and the wallet-URI checks in `tests/test_wallet.py`. A normal `pytest` run
exercises each with a fixed, bounded budget (the `dev` profile's 50 examples;
see `tests/conftest.py`). [HypoFuzz](https://hypofuzz.com/) — from the
Hypothesis author — runs those **same** tests as an adaptive, coverage-guided
fuzzer for as long as you let it, steering input generation toward unexplored
branches. There is no new harness: it reuses the `@given` tests we already have.

Fuzzing is **run locally or on a schedule, never as a blocking CI gate** — it
runs unbounded and is a search, not a pass/fail check. It complements (does not
replace) the "wide Hypothesis" budget work in
[#21](https://github.com/IvanAnishchuk/cuere/issues/21): that widens the
*in-suite* example budget; this explores beyond it.

## Running it

HypoFuzz lives in a dedicated `fuzz` dependency group, kept out of `dev` so the
CI `uv sync --dev` jobs stay lean. Opt in with `--group fuzz`:

```bash
uv sync --group fuzz                     # install hypofuzz + its deps
uv run --group fuzz hypothesis fuzz      # fuzz every Hypothesis test, with dashboard
```

`hypothesis fuzz` runs **forever** until stopped (Ctrl-C) and serves a live
dashboard (it prints the URL on startup). Anything after `--` is passed through
to pytest to select which tests to fuzz:

```bash
# Headless (no dashboard), two workers, only the renderer property tests:
uv run --group fuzz hypothesis fuzz --no-dashboard -n 2 -- tests/test_render_properties.py
```

## Triaging a failure

When HypoFuzz finds a falsifying example it saves it to the Hypothesis example
database (`.hypothesis/`, gitignored), exactly as an in-suite Hypothesis failure
would. The next plain `pytest` run **replays** it and fails, so the triage loop
is:

1. **Reproduce** — `uv run pytest <the failing test>` replays the saved example.
2. **Decide** — is it a real defect, or a property that is stricter than the
   contract? Fix the code, or relax the property.
3. **Pin it** — add the example as an explicit regression with Hypothesis's
   [`@example(...)`](https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.example)
   decorator so it is checked on every run, not only while the database happens
   to hold it.

## Current status

An initial bounded session (the 15 Hypothesis tests, two workers, a couple of
minutes) surfaced **no failing examples** — the renderer and wallet-URI
invariants held. This page is the workflow for the next person to repeat and
extend it. A non-blocking, cron-scheduled fuzz workflow is tracked in
[#92](https://github.com/IvanAnishchuk/cuere/issues/92).
