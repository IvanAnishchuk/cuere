"""Tests pinning the optimize_uri contract."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from cuere import QRMatrix, is_qr_alphanumeric, optimize_uri

BECH32_URI = "bitcoin:bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
TAPROOT_URI = "bitcoin:bc1p5d7rjq7g6rdk2yhzks9smlaqtedr4dekq08ge8ztwac72sfr9rusxg3297"
BASE58_URI = "bitcoin:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
WC_URI = "wc:7f6e504bfad60b485450578e05678ed3@2?relay-protocol=irn&symKey=587d5484ce2a2a6e"


def test_lowercase_bech32_uri_is_uppercased() -> None:
    assert optimize_uri(BECH32_URI) == BECH32_URI.upper()


def test_mixed_case_is_untouched() -> None:
    assert optimize_uri(BASE58_URI) == BASE58_URI


def test_query_string_is_untouched() -> None:
    uri = BECH32_URI + "?amount=0.1"
    assert optimize_uri(uri) == uri


def test_walletconnect_uri_is_untouched() -> None:
    assert optimize_uri(WC_URI) == WC_URI


def test_empty_string_is_untouched() -> None:
    assert optimize_uri("") == ""


def test_non_bech32_scheme_is_untouched() -> None:
    # ethereum: uses EIP-55 case-significant checksums — never uppercase it,
    # even when it is fully lowercase and alphanumeric.
    assert optimize_uri("ethereum:0xabcdef0123456789") == "ethereum:0xabcdef0123456789"
    assert optimize_uri("mailto:user") == "mailto:user"


def test_lightning_invoice_is_uppercased() -> None:
    uri = "lightning:lnbc1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqf"
    assert optimize_uri(uri) == uri.upper()


def test_optimized_uri_never_grows_the_qr() -> None:
    for uri in (BECH32_URI, TAPROOT_URI, BASE58_URI, WC_URI):
        original = QRMatrix.encode(uri)
        optimized = QRMatrix.encode(optimize_uri(uri))
        assert isinstance(original.version, int)
        assert isinstance(optimized.version, int)
        assert optimized.version <= original.version


def test_uppercasing_shrinks_a_taproot_uri() -> None:
    original = QRMatrix.encode(TAPROOT_URI)
    optimized = QRMatrix.encode(optimize_uri(TAPROOT_URI))
    assert isinstance(original.version, int)
    assert isinstance(optimized.version, int)
    assert optimized.version < original.version


def test_is_qr_alphanumeric() -> None:
    assert is_qr_alphanumeric("BITCOIN:BC1Q $%*+-./:")
    assert not is_qr_alphanumeric("")
    assert not is_qr_alphanumeric("lowercase")
    assert not is_qr_alphanumeric("WITH?QUERY")
    assert not is_qr_alphanumeric("UNDER_SCORE")


@given(st.text(max_size=60))
def test_optimize_uri_is_idempotent(uri: str) -> None:
    once = optimize_uri(uri)
    assert optimize_uri(once) == once


@given(st.text(alphabet="0123456789abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=60))
def test_lowercase_bitcoin_uri_round_trips_through_upper(suffix: str) -> None:
    uri = f"bitcoin:{suffix}"
    assert optimize_uri(uri) == uri.upper()
