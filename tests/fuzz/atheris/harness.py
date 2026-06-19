"""Shared bootstrap for the Atheris fuzz targets.

Importing this module gives a fuzz target a ready-to-use ``atheris`` — the
coverage-guided, libFuzzer-based fuzzer (Apache-2.0, so unlike the proprietary
HypoFuzz it is an allow-listed declared dependency; see ``docs/fuzzing.md``) —
plus the two helpers every target needs, so the bootstrap lives here once
instead of being copy-pasted: ``instrument`` (instrument cuere for coverage
feedback) and ``run`` (wire the target to libFuzzer and start fuzzing).

Atheris >=3.1 supports Python 3.11-3.14, so no version shim is needed on either
of cuere's supported runtimes (CI tests 3.13 and 3.14). Install the fuzzer with
``uv sync --group fuzz`` and run a target as a script (never imported by the
default test run) — Python puts the script's own directory on ``sys.path``, so
``from harness import ...`` resolves with no path juggling. A target's whole
prologue is then:

    from harness import atheris, instrument, run

    with instrument():
        from cuere import render_matrix

    def fuzz_target(data: bytes) -> None:
        fdp = atheris.FuzzedDataProvider(data)
        ...

    run(fuzz_target)
"""

import sys
from collections.abc import Callable, Iterable

import atheris

__all__ = ["atheris", "instrument", "run"]

# Instrument only cuere (not the stdlib or deps): coverage feedback should steer
# the fuzzer toward project code. Centralised here so changing the scope is one
# edit, not one per target.
_INCLUDE = ("cuere",)


def instrument(include: Iterable[str] = _INCLUDE):
    """Instrument `include` (default: cuere) — use around a target's cuere imports."""
    return atheris.instrument_imports(include=list(include))


def run(fuzz_target: Callable[[bytes], None]) -> None:
    """Wire `fuzz_target` to libFuzzer and start fuzzing (does not return)."""
    atheris.Setup(sys.argv, fuzz_target)
    atheris.Fuzz()
