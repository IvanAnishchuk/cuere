"""Property-based round-trip tests for the renderers."""

from __future__ import annotations

import re

from hypothesis import given
from hypothesis import strategies as st

from cuere import QRMatrix, RenderMode, render_height, render_matrix, render_width

QR_ALPHANUMERIC = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
_GLYPH_TO_PAIR = {" ": (False, False), "▀": (True, False), "▄": (False, True), "█": (True, True)}
_SGR = re.compile(r"\x1b\[[0-9;]*m")


@st.composite
def matrices(draw: st.DrawFn) -> QRMatrix:
    width = draw(st.integers(min_value=1, max_value=40))
    height = draw(st.integers(min_value=1, max_value=40))
    rows = draw(
        st.lists(
            st.lists(st.booleans(), min_size=width, max_size=width),
            min_size=height,
            max_size=height,
        )
    )
    return QRMatrix(modules=tuple(tuple(row) for row in rows), version=1, border=0)


def _parse_half(text: str) -> tuple[tuple[bool, ...], ...]:
    rows: list[tuple[bool, ...]] = []
    for line in text.split("\n"):
        pairs = [_GLYPH_TO_PAIR[char] for char in line]
        rows.append(tuple(top for top, _ in pairs))
        rows.append(tuple(bottom for _, bottom in pairs))
    return tuple(rows)


def _parse_block(text: str) -> tuple[tuple[bool, ...], ...]:
    rows: list[tuple[bool, ...]] = []
    for line in text.split("\n"):
        assert len(line) % 2 == 0
        rows.append(tuple(line[i : i + 2] == "██" for i in range(0, len(line), 2)))
    return tuple(rows)


@given(matrices())
def test_half_round_trip(matrix: QRMatrix) -> None:
    recovered = _parse_half(render_matrix(matrix))
    assert recovered[: matrix.height] == matrix.modules
    if matrix.height % 2:  # the padding row must be all-light
        assert not any(recovered[matrix.height])


@given(matrices())
def test_block_round_trip(matrix: QRMatrix) -> None:
    assert _parse_block(render_matrix(matrix, mode=RenderMode.BLOCK)) == matrix.modules


@given(matrices())
def test_ansi_stripped_equals_half(matrix: QRMatrix) -> None:
    ansi = render_matrix(matrix, mode=RenderMode.ANSI)
    assert _SGR.sub("", ansi) == render_matrix(matrix)


@given(matrices(), st.sampled_from(list(RenderMode)))
def test_invert_matches_inverted_matrix(matrix: QRMatrix, mode: RenderMode) -> None:
    assert render_matrix(matrix, mode=mode, invert=True) == render_matrix(
        matrix.inverted(), mode=mode
    )


@given(matrices())
def test_double_invert_is_identity(matrix: QRMatrix) -> None:
    assert matrix.inverted().inverted() == matrix


@given(matrices(), st.sampled_from(list(RenderMode)))
def test_dimensions_match_render(matrix: QRMatrix, mode: RenderMode) -> None:
    lines = render_matrix(matrix, mode=mode).split("\n")
    assert len(lines) == render_height(matrix, mode)
    widths = {len(_SGR.sub("", line)) for line in lines}
    assert widths == {render_width(matrix, mode)}


@given(st.text(alphabet=QR_ALPHANUMERIC, min_size=1, max_size=100))
def test_encoding_alphanumeric_text_always_works(text: str) -> None:
    matrix = QRMatrix.encode(text)
    assert matrix.width == matrix.height == matrix.size
    inner = matrix.size - 2 * matrix.border
    assert inner >= 21
    assert (inner - 21) % 4 == 0
