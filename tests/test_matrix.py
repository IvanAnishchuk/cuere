"""Tests for the segno-wrapping encoding layer."""

from __future__ import annotations

import dataclasses

import pytest

from cuere import ECLevel, EncodingError, QRMatrix
from cuere.matrix import coerce

V1_SIZE = 21  # modules per side of a version-1 QR code


def test_hello_is_version_one() -> None:
    matrix = QRMatrix.encode("HELLO")
    assert matrix.version == 1
    assert matrix.size == V1_SIZE + 2 * 4
    assert matrix.border == 4


@pytest.mark.parametrize("border", [0, 1, 4, 7])
def test_border_is_baked_into_size(border: int) -> None:
    matrix = QRMatrix.encode("HELLO", border=border)
    assert matrix.size == V1_SIZE + 2 * border


def test_matrix_is_square() -> None:
    matrix = QRMatrix.encode("HELLO WORLD", border=2)
    assert matrix.height == matrix.width == matrix.size
    assert all(len(row) == matrix.size for row in matrix.modules)


def test_bytes_input() -> None:
    matrix = QRMatrix.encode(b"\x00\x01\x02binary")
    assert matrix.size > 0


def test_micro_qr_version_is_a_string() -> None:
    matrix = QRMatrix.encode("1234", micro=True)
    assert isinstance(matrix.version, str)
    assert matrix.version.startswith("M")


def test_higher_error_level_grows_the_code() -> None:
    low = QRMatrix.encode("A" * 60, error="L")
    high = QRMatrix.encode("A" * 60, error="H")
    assert isinstance(low.version, int)
    assert isinstance(high.version, int)
    assert high.version > low.version


def test_error_level_accepts_enum_and_string() -> None:
    assert QRMatrix.encode("HI", error=ECLevel.M) == QRMatrix.encode("HI", error="M")


def test_overflow_raises_encoding_error() -> None:
    with pytest.raises(EncodingError):
        _ = QRMatrix.encode("A" * 8000, error="H")


def test_bad_error_level_raises_encoding_error() -> None:
    with pytest.raises(EncodingError):
        _ = QRMatrix.encode("HELLO", error="X")


def test_negative_border_raises_encoding_error() -> None:
    with pytest.raises(EncodingError):
        _ = QRMatrix.encode("HELLO", border=-1)


def test_boost_error_can_change_the_matrix() -> None:
    # boost_error=False is the deliberate default (smallest code on screen);
    # boosting raises the EC level when there is spare capacity.
    plain = QRMatrix.encode("HI", boost_error=False)
    boosted = QRMatrix.encode("HI", boost_error=True)
    assert plain.modules != boosted.modules


def test_inverted_is_an_involution() -> None:
    matrix = QRMatrix.encode("HELLO")
    assert matrix.inverted() != matrix
    assert matrix.inverted().inverted() == matrix


def test_inverted_flips_every_module() -> None:
    matrix = QRMatrix.encode("HELLO", border=0)
    flipped = matrix.inverted()
    for row, flipped_row in zip(matrix.modules, flipped.modules, strict=True):
        assert [not m for m in row] == list(flipped_row)


def test_frozen() -> None:
    matrix = QRMatrix.encode("HELLO")
    with pytest.raises(dataclasses.FrozenInstanceError):
        # Dunder call instead of plain assignment so the deliberate type
        # error stays invisible to mypy/ty/basedpyright alike.
        matrix.__setattr__("border", 5)


def test_empty_matrix_dimensions() -> None:
    matrix = QRMatrix(modules=(), version=1, border=0)
    assert matrix.width == 0
    assert matrix.height == 0


def test_coerce_passes_matrices_through() -> None:
    matrix = QRMatrix.encode("HELLO")
    assert coerce(matrix) is matrix


def test_coerce_encodes_strings() -> None:
    assert coerce("HELLO") == QRMatrix.encode("HELLO")
