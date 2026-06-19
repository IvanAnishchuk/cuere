"""Atheris fuzz target for the cuere renderers.

Builds an arbitrary QR module grid from the fuzzer's bytes and renders it in
every mode, asserting the renderer's round-trip and dimension invariants — the
same properties tests/test_render_properties.py checks with Hypothesis, but
driven here by libFuzzer coverage feedback.

    uv run --group fuzz python tests/fuzz/atheris/fuzz_render.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harness import atheris

with atheris.instrument_imports(include=["cuere"]):
    from cuere import (
        QRMatrix,
        RenderMode,
        render_height,
        render_matrix,
        render_svg,
        render_width,
    )

_GLYPH_TO_PAIR = {" ": (False, False), "▀": (True, False), "▄": (False, True), "█": (True, True)}
_MODES = list(RenderMode)
_MAX_SIDE = 40


def _parse_half(text: str) -> tuple[tuple[bool, ...], ...]:
    """Recover the module grid from HALF-mode output (two rows per glyph line)."""
    rows: list[tuple[bool, ...]] = []
    for line in text.split("\n"):
        pairs = [_GLYPH_TO_PAIR[char] for char in line]
        rows.append(tuple(top for top, _ in pairs))
        rows.append(tuple(bottom for _, bottom in pairs))
    return tuple(rows)


def fuzz_target(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    width = fdp.ConsumeIntInRange(1, _MAX_SIDE)
    height = fdp.ConsumeIntInRange(1, _MAX_SIDE)
    raw = fdp.ConsumeBytes(width * height)
    cells = [bool(byte & 1) for byte in raw]
    cells.extend([False] * (width * height - len(cells)))
    modules = tuple(tuple(cells[r * width : (r + 1) * width]) for r in range(height))
    matrix = QRMatrix(modules=modules, version=1, border=0)

    invert = fdp.ConsumeBool()
    expected = matrix.inverted().modules if invert else modules

    # HALF mode round-trips the grid; an odd height pads one all-light row.
    recovered = _parse_half(render_matrix(matrix, mode=RenderMode.HALF, invert=invert))
    assert recovered[:height] == expected
    if height % 2:
        assert not any(recovered[height])

    # Every mode: the rendered line count matches the predicted height, no crash.
    for mode in _MODES:
        rendered = render_matrix(matrix, mode=mode, invert=invert)
        assert len(rendered.split("\n")) == render_height(matrix, mode)

    render_svg(matrix, invert=invert)
    render_width(matrix)


atheris.Setup(sys.argv, fuzz_target)
atheris.Fuzz()
