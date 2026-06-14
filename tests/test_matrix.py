"""Tests for the segno-wrapping encoding layer."""

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


@pytest.mark.parametrize("border", [0, 1, 4, 7, 64])
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


@pytest.mark.parametrize(
    ("data", "error", "expected"),
    [
        ("12345", "L", "M2"),  # numeric
        ("A1B2", "L", "M2"),  # alphanumeric
        ("ABCDEFGH", "M", "M3"),  # larger alnum + M correction
        ("hello world", "L", "M4"),  # byte mode (lowercase) needs the largest micro
        ("12345", "Q", "M4"),  # Q correction only exists at M4
    ],
)
def test_reachable_micro_variants(data: str, error: str, expected: str) -> None:
    # The micro sizes cuere can actually produce, one payload per variant.
    assert QRMatrix.encode(data, micro=True, error=error).version == expected


def test_micro_default_error_level_skips_m1() -> None:
    # M1 carries no error correction, but cuere always passes an explicit level
    # (default L), so the smallest reachable micro code is M2, never M1.
    assert QRMatrix.encode("1", micro=True).version == "M2"


def test_micro_rejects_high_error_level() -> None:
    # Micro QR has no H level; segno raises and cuere wraps it as EncodingError.
    with pytest.raises(EncodingError):
        _ = QRMatrix.encode("12345", micro=True, error="H")


def test_micro_rejects_oversized_payload() -> None:
    # No micro variant can hold this; the overflow surfaces as EncodingError.
    with pytest.raises(EncodingError):
        _ = QRMatrix.encode("A" * 40, micro=True)


def test_empty_payload_encodes() -> None:
    # segno encodes an empty payload as a valid version-1 code (it is not an
    # overflow), so cuere must not treat empty input as an error.
    assert QRMatrix.encode("").version == 1
    assert QRMatrix.encode(b"").version == 1


def test_whitespace_payload_encodes_and_differs_from_empty() -> None:
    assert QRMatrix.encode(" ").version == 1
    assert QRMatrix.encode("\n").version == 1
    assert QRMatrix.encode(" ") != QRMatrix.encode("")


def test_large_payload_encodes_to_high_version() -> None:
    # A near-maximal valid payload stays a square, well-formed matrix many
    # versions above 1 (the opposite boundary from the overflow test).
    matrix = QRMatrix.encode("A" * 1000, error="L")
    assert isinstance(matrix.version, int)
    assert matrix.version >= 15
    assert matrix.height == matrix.width == matrix.size
    inner = matrix.size - 2 * matrix.border
    assert (inner - 21) % 4 == 0  # a valid QR side length


def test_higher_error_level_grows_the_code() -> None:
    low = QRMatrix.encode("A" * 60, error="L")
    high = QRMatrix.encode("A" * 60, error="H")
    assert isinstance(low.version, int)
    assert isinstance(high.version, int)
    assert high.version > low.version


@pytest.mark.parametrize("error", list(ECLevel))
def test_error_level_enum_and_string_agree(error: ECLevel) -> None:
    # Every level encodes, and the enum and its string value are interchangeable.
    assert QRMatrix.encode("HELLO", error=error) == QRMatrix.encode("HELLO", error=error.value)


def test_error_level_version_is_monotonic() -> None:
    # More error correction never shrinks the code: for a payload that spans
    # several versions, the version is non-decreasing from L through H.
    payload = "HELLO WORLD " * 5
    versions: list[int] = []
    for error in ECLevel:
        version = QRMatrix.encode(payload, error=error).version
        assert isinstance(version, int)
        versions.append(version)
    assert versions == sorted(versions)


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
