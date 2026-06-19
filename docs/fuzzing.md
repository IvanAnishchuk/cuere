# Fuzzing and deep property testing

How cuere explores its renderers and wallet-URI builders beyond the everyday
test run — and which coverage-guided fuzzing tools it does (and does not) adopt,
and why.

## What's already in place

cuere's correctness rests on three layers that run on every change:

- **Property-based tests** ([Hypothesis](https://hypothesis.works/)) in
  `tests/test_render_properties.py` and `tests/test_wallet.py`. They round-trip
  arbitrary bit-grids *and* real segno encoder output through the renderers, and
  exercise the wallet-URI builders / `optimize_uri` over generated inputs. The
  default `dev` profile draws 50 examples per test; selection is by
  `HYPOTHESIS_PROFILE` (`tests/conftest.py`).
- **100% branch coverage**, enforced in CI (`fail_under = 100`). Every branch is
  executed by the suite *by construction*.
- **[Mutation testing](mutation-testing.md)** (mutmut, dev-only) — proof that the
  assertions, not just the coverage, would catch a behavioral change.

Coverage-guided fuzzing is a fourth, deeper layer: instead of drawing inputs
blindly, it uses execution feedback to steer toward inputs that reach new states.
The question this page answers is *which* OSS tool, if any, is worth adopting for
that — given the layers above already make cuere's covered code hard to surprise.

!!! note "HypoFuzz is a personal local aid, not a project tool"
    [HypoFuzz](https://hypofuzz.com/) runs the existing Hypothesis tests as a
    coverage-guided fuzzer with **zero new harness**, which is ideal — but it is
    **proprietary** (`LicenseRef-HypoFuzz`: free for non-commercial / open-source
    use, no redistribution, commercial/CI use needs a paid licence). Declaring it
    in `pyproject.toml` / `uv.lock` would publish it into the dependency graph and
    trip the `dependency-review` licence gate. It is therefore deliberately **not**
    a declared dependency — it lives only in an uncommitted, git-ignored
    `fuzz-local.sh` that installs it transiently (`uv run --with hypofuzz …`). See
    [#37](https://github.com/IvanAnishchuk/cuere/issues/37). This page evaluates an
    **OSS-licensed** path to the same goal.

## Options evaluated

| Option | Licence | Reuses `@given` tests? | Dependency weight | Fit |
|--------|---------|------------------------|-------------------|-----|
| **Wide Hypothesis profile** | MPL-2.0 *(already a dependency)* | ✅ directly | none | High — pure-OSS, no new harness |
| **[Atheris](https://github.com/google/atheris)** (Google) | Apache-2.0 *(allow-listed)* | ❌ needs a `TestOneInput(bytes)` harness | heavy — native, clang/libFuzzer build | Moderate — genuine coverage feedback, at a real cost |
| **[OSS-Fuzz](https://google.github.io/oss-fuzz/)** (service) | n/a | ❌ Atheris harness | n/a | No — admission requires significant userbase / criticality |

**Wide Hypothesis profile** — a high-`max_examples`, generous-`deadline` profile
that reuses the existing property tests and runs non-blocking (scheduled and/or
local), keeping the per-PR suite fast. Cheapest possible adoption: Hypothesis is
already a dependency, and there is no second input-generation surface to maintain.

**Atheris** — a libFuzzer-based, genuinely coverage-guided fuzzer. It does **not**
consume `@given` tests; it needs a separate `TestOneInput(data: bytes)` harness
(typically via `FuzzedDataProvider`). Its licence (Apache-2.0) **passes** the
`dependency-review` allow-list, so — unlike HypoFuzz — it is not blocked on
licensing. The cost is elsewhere: it is a heavy native dependency (clang/libFuzzer
at build) and a second input-generation surface to maintain alongside the
Hypothesis strategies.

**OSS-Fuzz** — Google's continuous-fuzzing *service*. It builds on Atheris
harnesses and is aimed at projects with a significant user base or critical role;
cuere would not currently qualify, so it is out of scope here.

## Decision

cuere pursues both **OSS** paths as tracked follow-ups, and keeps HypoFuzz as a
personal local aid only:

1. **Pilot Atheris first** — [#96](https://github.com/IvanAnishchuk/cuere/issues/96).
   Add a minimal harness for the highest-value targets (the renderers and the
   wallet-URI builders), keep it dev/local-only or a non-blocking scheduled job,
   and **record a keep-or-drop verdict here** once measured. Because cuere already
   enforces 100% branch coverage, the upside is bounded to finding *bad values
   within already-covered branches*, so the pilot must demonstrate value beyond
   the existing Hypothesis suite to earn a permanent place.
2. **Add a wide Hypothesis profile** —
   [#97](https://github.com/IvanAnishchuk/cuere/issues/97). The low-cost,
   zero-new-dependency companion: a `nightly`-style profile reusing the existing
   property tests, run off the blocking PR path.
3. **HypoFuzz stays local** — proprietary, never a declared dependency
   ([#37](https://github.com/IvanAnishchuk/cuere/issues/37)).
4. **OSS-Fuzz is not pursued** at cuere's current scale.

As part of recording this decision, the dead `ci` Hypothesis profile (registered
at 200 examples but never selected) was removed from `tests/conftest.py`; the real
wide profile lands with #97.

!!! note "What would change the Atheris verdict"
    If a pilot surfaces a class of defects the Hypothesis suite misses — for
    example in input parsing or byte-level handling that benefits from libFuzzer's
    state exploration — the native-dependency cost becomes worth paying and Atheris
    graduates from pilot to a standing (non-blocking) job. If it only reconfirms
    what the property tests already cover, the wide Hypothesis profile is the
    better long-term home and the pilot is retired.
