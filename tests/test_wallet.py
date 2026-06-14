"""Tests pinning the optimize_uri contract."""

import string
from decimal import Decimal
from urllib.parse import unquote

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cuere import (
    CuereError,
    QRMatrix,
    WalletURIError,
    bitcoin_uri,
    is_qr_alphanumeric,
    optimize_uri,
    render,
)

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


def test_scheme_without_colon_is_untouched() -> None:
    # A bare word (no ":") is not a URI we recognize; leave it alone.
    assert optimize_uri("bitcoin") == "bitcoin"


def test_scheme_parsed_at_first_colon() -> None:
    # The scheme is whatever precedes the *first* colon (URI semantics), so a
    # colon inside the payload must not hide the bitcoin: scheme.
    assert optimize_uri("bitcoin:abc:def") == "BITCOIN:ABC:DEF"


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


# --- bitcoin_uri (BIP-21) -------------------------------------------------

BECH32_ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
BASE58_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
# The full alphabet bitcoin_uri accepts in an address (base58 + bech32 are subsets).
ADDRESS_ALPHABET = string.ascii_letters + string.digits


def test_bare_address_has_no_query() -> None:
    assert bitcoin_uri(BECH32_ADDRESS) == f"bitcoin:{BECH32_ADDRESS}"


def test_bip21_canonical_example() -> None:
    # The example from BIP-21 itself, byte-for-byte.
    uri = bitcoin_uri(
        BASE58_ADDRESS, amount=Decimal("20.3"), label="Luke-Jr", message="Donation for project xyz"
    )
    assert uri == (
        f"bitcoin:{BASE58_ADDRESS}?amount=20.3&label=Luke-Jr&message=Donation%20for%20project%20xyz"
    )


def test_params_appear_in_fixed_order() -> None:
    uri = bitcoin_uri(BECH32_ADDRESS, message="m", label="l", amount=1)
    assert uri == f"bitcoin:{BECH32_ADDRESS}?amount=1&label=l&message=m"


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (50, "50"),  # int
        (Decimal("0.1"), "0.1"),  # Decimal
        ("0.5", "0.5"),  # str
        (Decimal("1E-7"), "0.0000001"),  # no scientific notation leaks
        (Decimal("0.00000001"), "0.00000001"),  # exactly one satoshi is allowed
        (Decimal("1.0"), "1.0"),  # trailing zero preserved, not normalized away
        (Decimal("0.500000000"), "0.500000000"),  # 9 trailing-zero digits is still 0.5 BTC
        ("0.12345678", "0.12345678"),  # eight significant fractional digits is allowed
    ],
)
def test_amount_formatting(amount: Decimal | int | str, expected: str) -> None:
    assert bitcoin_uri(BECH32_ADDRESS, amount=amount) == (
        f"bitcoin:{BECH32_ADDRESS}?amount={expected}"
    )


def test_label_and_message_are_percent_encoded() -> None:
    uri = bitcoin_uri(BECH32_ADDRESS, label="Coffee & Cake", message="50% off = win")
    assert uri == (
        f"bitcoin:{BECH32_ADDRESS}?label=Coffee%20%26%20Cake&message=50%25%20off%20%3D%20win"
    )
    # And the encoding is reversible back to the original free text.
    query = uri.partition("?")[2]
    parts = dict(pair.split("=", 1) for pair in query.split("&"))
    assert unquote(parts["label"]) == "Coffee & Cake"
    assert unquote(parts["message"]) == "50% off = win"


def test_empty_label_is_kept_but_none_is_omitted() -> None:
    # None means "omit"; an explicit empty string means "present but empty".
    assert bitcoin_uri(BECH32_ADDRESS, label="") == f"bitcoin:{BECH32_ADDRESS}?label="
    assert bitcoin_uri(BECH32_ADDRESS) == f"bitcoin:{BECH32_ADDRESS}"


@pytest.mark.parametrize("address", [BECH32_ADDRESS, BASE58_ADDRESS, "tb1qxyz", "12345"])
def test_valid_address_alphabets_are_accepted(address: str) -> None:
    assert bitcoin_uri(address) == f"bitcoin:{address}"


@pytest.mark.parametrize(
    "address", ["", "bad addr", "bc1q?x", "bc1:q", "addr&more", "bc1q%41", "naïve"]
)
def test_invalid_address_is_rejected(address: str) -> None:
    with pytest.raises(WalletURIError):
        _ = bitcoin_uri(address)


@pytest.mark.parametrize(
    "amount",
    [
        "not-a-number",  # unparseable
        Decimal("NaN"),  # not finite
        Decimal("Infinity"),  # not finite
        0,  # not positive
        Decimal("-1"),  # not positive
        "0.000000001",  # 9 significant decimals: finer than a satoshi
        True,  # bool is an int subtype but must not be treated as amount=1
        False,  # likewise: a bool is never a valid amount
    ],
)
def test_invalid_amount_is_rejected(amount: Decimal | int | str) -> None:
    with pytest.raises(WalletURIError):
        _ = bitcoin_uri(BECH32_ADDRESS, amount=amount)


def test_error_is_a_cuere_error_and_carries_the_value() -> None:
    assert issubclass(WalletURIError, CuereError)
    with pytest.raises(WalletURIError) as exc_info:
        _ = bitcoin_uri("bad addr")
    assert exc_info.value.value == "bad addr"


def test_composes_with_optimize_uri_when_there_is_no_query() -> None:
    # A bare lowercase bech32 address is QR-alphanumeric once uppercased.
    assert optimize_uri(bitcoin_uri(BECH32_ADDRESS)) == f"bitcoin:{BECH32_ADDRESS}".upper()


def test_optimize_uri_leaves_a_uri_with_a_query_alone() -> None:
    # A query string is not QR-alphanumeric, so optimize_uri must not touch it.
    uri = bitcoin_uri(BECH32_ADDRESS, amount=1)
    assert optimize_uri(uri) == uri


def test_composes_with_render_and_encode() -> None:
    uri = bitcoin_uri(BECH32_ADDRESS, amount=Decimal("0.5"), label="tip")
    assert isinstance(render(uri), str)
    assert isinstance(QRMatrix.encode(uri).version, int)


@given(st.text(alphabet=ADDRESS_ALPHABET, min_size=1))
def test_bare_address_round_trips(address: str) -> None:
    assert bitcoin_uri(address) == f"bitcoin:{address}"


@given(st.text(min_size=0, max_size=40))
def test_label_round_trips_through_percent_encoding(label: str) -> None:
    uri = bitcoin_uri(BECH32_ADDRESS, label=label)
    encoded = uri.partition("label=")[2]
    assert unquote(encoded) == label
