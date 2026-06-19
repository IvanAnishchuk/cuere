"""Shared bootstrap for the Atheris fuzz targets.

Importing this module gives a fuzz target a ready-to-use ``atheris`` — the
coverage-guided, libFuzzer-based fuzzer (Apache-2.0, so unlike the proprietary
HypoFuzz it is an allow-listed declared dependency; see ``docs/fuzzing.md``).

Atheris >=3.1 supports Python 3.11-3.14, so no version shim is needed on either
of cuere's supported runtimes (CI tests 3.13 and 3.14). Install the fuzzer with
``uv sync --group fuzz`` and run a target as a script (never imported by the
default test run):

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from harness import atheris  # noqa: E402

    with atheris.instrument_imports(include=["cuere"]):
        from cuere import render_matrix

    def fuzz_target(data: bytes) -> None:
        fdp = atheris.FuzzedDataProvider(data)
        ...

    atheris.Setup(sys.argv, fuzz_target)
    atheris.Fuzz()
"""

import atheris

__all__ = ["atheris"]
