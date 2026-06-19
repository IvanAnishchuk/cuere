"""Pytest wrapper that runs each Atheris fuzz target as a short smoke test.

Discovers tests/fuzz/atheris/fuzz_*.py and runs each for a configurable time
(FUZZ_SECONDS env, default 10s), passing if the target explores without
crashing. This is NOT part of the default test run: it is gated behind the
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
# Targets with a known, unfixed crash are skipped here (linked to the tracking
# issue) so the smoke test stays deterministic — the fuzzer only rediscovers a
# crash probabilistically within the time box, which would make xfail flaky.
# TODO(#99): drop this once the wallet huge-exponent MemoryError is fixed.
_KNOWN_CRASHES = {
    "fuzz_wallet": "MemoryError on huge-exponent amount/value — see #99",
}
_DEFAULT_SECONDS = 10
# Exit codes that are NOT crashes: 0 = the target exited cleanly; 124 = the
# `timeout` wrapper hit the time limit (the normal outcome — the fuzzer runs
# until killed). -15 is kept defensively for a direct SIGTERM (e.g. from a CI
# runner); via `timeout` the parent sees 124, since `timeout` reaps the child.
_OK_RETURNCODES = (0, 124, -15)


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
    """Run one Atheris target under a time box; pass if it does not crash."""
    target_path = _ATHERIS_DIR / f"{target}.py"
    result = subprocess.run(
        ["timeout", str(fuzz_seconds), sys.executable, str(target_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in _OK_RETURNCODES:
        pytest.fail(
            f"Atheris target {target} crashed (exit {result.returncode}):\n"
            f"{result.stdout[-1000:]}\n{result.stderr[-1000:]}"
        )
