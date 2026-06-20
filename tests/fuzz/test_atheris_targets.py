"""Pytest wrapper that runs each Atheris fuzz target as a short smoke test.

Discovers tests/fuzz/atheris/fuzz_*.py and runs each for a configurable time
(FUZZ_SECONDS env, default 10s), passing only if the target actually fuzzes for
the whole time box without crashing. This is NOT part of the default test run:
it is gated behind the
``atheris`` marker and needs the fuzzer installed (``uv sync --group fuzz``).
``--no-cov`` because the targets fuzz in subprocesses, so the suite's 100%
in-process coverage gate does not apply here.

    uv run --group fuzz pytest tests/fuzz -m atheris --no-cov
    FUZZ_SECONDS=120 uv run --group fuzz pytest tests/fuzz -m atheris --no-cov
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_ATHERIS_DIR = Path(__file__).parent / "atheris"
_TARGETS = sorted(path.stem for path in _ATHERIS_DIR.glob("fuzz_*.py"))
# Targets with a known, unfixed crash are skipped here (keyed by stem, valued by
# a "<reason> — see #NN" note) so the smoke test stays deterministic — the fuzzer
# only rediscovers a crash probabilistically within the time box, which would make
# xfail flaky. Empty now that #99 (the wallet huge-exponent MemoryError) is fixed;
# add an entry, linked to its tracking issue, when a target finds a new crash.
_KNOWN_CRASHES: dict[str, str] = {}
_DEFAULT_SECONDS = 10
# A healthy run fuzzes until the `timeout` wrapper kills it at the time box, so
# `timeout` reports 124 (or -15 if it ever reaps a direct SIGTERM). Any *self*-
# chosen exit — including a clean 0 — means the target stopped before the box: a
# crash, or a no-op harness that never fuzzed. Only the timed-out codes pass.
# (A crash normally exits non-124 well before the box; the rare crash whose
# handler hangs past the box, still 124, is a known blind spot — accepted.)
_TIMED_OUT_RETURNCODES = (124, -15)
# libFuzzer prints this once it has run the seed inputs — proof the fuzz loop
# actually started. Its absence in a timed-out run means the harness hung before
# fuzzing (instrumentation error, import failure), i.e. it explored nothing.
_RAN_MARKER = "INITED"


@pytest.fixture
def fuzz_seconds() -> int:
    """Seconds to run each target — the FUZZ_SECONDS env var, default 10."""
    return int(os.environ.get("FUZZ_SECONDS", str(_DEFAULT_SECONDS)))


# TODO: `_param` has no return annotation — `pytest.param()` exposes no public
# return type (`pytest.ParameterSet` does not exist), and this file is excluded
# from the type checkers, so any annotation would be cosmetic. Flagged in the PR
# for human review: accept as-is, or annotate via the private
# `_pytest.mark.structures.ParameterSet`.
def _param(stem: str):
    """Wrap a target name, skipping it if it has a known unfixed crash."""
    if stem in _KNOWN_CRASHES:
        return pytest.param(stem, marks=pytest.mark.skip(reason=_KNOWN_CRASHES[stem]))
    return pytest.param(stem)


@pytest.mark.atheris
@pytest.mark.parametrize("target", [_param(stem) for stem in _TARGETS])
def test_atheris_target(target: str, fuzz_seconds: int) -> None:
    """Run one Atheris target under a time box; pass only if it fuzzed and did not crash."""
    target_path = _ATHERIS_DIR / f"{target}.py"
    result = subprocess.run(
        ["timeout", str(fuzz_seconds), sys.executable, str(target_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in _TIMED_OUT_RETURNCODES:
        pytest.fail(
            f"Atheris target {target} exited before the time box (exit "
            f"{result.returncode}) — a crash or a harness that never fuzzed:\n"
            f"{result.stdout[-1000:]}\n{result.stderr[-1000:]}"
        )
    if _RAN_MARKER not in result.stderr:
        pytest.fail(
            f"Atheris target {target} was killed at the time box but never "
            f"started fuzzing (no {_RAN_MARKER!r} in libFuzzer output) — the "
            f"harness is not exercising the target:\n{result.stderr[-1000:]}"
        )
