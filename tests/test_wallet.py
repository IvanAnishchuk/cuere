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
    SchemeCase,
    WalletURIError,
    bitcoin_uri,
    erc20_transfer_uri,
    ethereum_uri,
    is_qr_alphanumeric,
    lightning_uri,
    optimize_uri,
    render,
    scheme_case,
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


# --- scheme_case (the public optimize_uri scheme classifier) --------------


def test_scheme_case_enum_has_the_three_documented_members() -> None:
    assert {member.name for member in SchemeCase} == {"INSENSITIVE", "SIGNIFICANT", "UNKNOWN"}


@pytest.mark.parametrize(
    ("uri", "expected"),
    [
        (BECH32_URI, SchemeCase.INSENSITIVE),  # bitcoin: — bech32, foldable
        ("lightning:lnbc1abc", SchemeCase.INSENSITIVE),
        ("BITCOIN:BC1Q", SchemeCase.INSENSITIVE),  # scheme matched case-insensitively
        ("ethereum:0xabc", SchemeCase.SIGNIFICANT),  # EIP-55 case carries meaning
        (WC_URI, SchemeCase.SIGNIFICANT),  # wc: recognized explicitly, not UNKNOWN
        ("mailto:user", SchemeCase.UNKNOWN),  # a real scheme cuere does not know
        ("bitcoin", SchemeCase.UNKNOWN),  # no ":" -> no scheme
        ("", SchemeCase.UNKNOWN),
    ],
)
def test_scheme_case_classifies_each_scheme(uri: str, expected: SchemeCase) -> None:
    assert scheme_case(uri) is expected


def test_walletconnect_is_recognized_as_case_significant_not_unknown() -> None:
    # The crux of #29: wc: is recognized *explicitly* as case-significant —
    # distinct from an unknown scheme even though both are passed through.
    assert scheme_case(WC_URI) is SchemeCase.SIGNIFICANT


def test_optimize_uri_folds_exactly_the_case_insensitive_schemes() -> None:
    # optimize_uri's gate is precisely "scheme_case(uri) is INSENSITIVE".
    for uri in (BECH32_URI, "lightning:lnbc1abc"):
        assert scheme_case(uri) is SchemeCase.INSENSITIVE
        assert optimize_uri(uri) == uri.upper()
    for uri in ("ethereum:0xabc", WC_URI, "mailto:user", "bitcoin"):
        assert scheme_case(uri) is not SchemeCase.INSENSITIVE
        assert optimize_uri(uri) == uri


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


# --- lightning_uri (BOLT11 / LNURL / BOLT12) ------------------------------

# Structurally valid (truncated) bech32 lightning payloads of each kind.
BOLT11_INVOICE = "lnbc1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqf"
LNURL = "lnurl1dp68gurn8ghj7um9wfmxjcm99e3k7mf0v9cxj0m385ekvcenxc6r2c35xvukxefcv5mkv"
BOLT12_OFFER = "lno1pqqkgz3zxyceqcfqqqqx5w6m"


def test_lightning_uri_prefixes_the_scheme() -> None:
    assert lightning_uri(BOLT11_INVOICE) == f"lightning:{BOLT11_INVOICE}"


@pytest.mark.parametrize("payload", [BOLT11_INVOICE, LNURL, BOLT12_OFFER])
def test_lightning_uri_accepts_bech32_lightning_payloads(payload: str) -> None:
    assert lightning_uri(payload) == f"lightning:{payload}"


def test_lightning_uri_accepts_an_all_uppercase_payload_verbatim() -> None:
    # bech32 may be all-upper (already QR-alphanumeric); it is kept verbatim.
    upper = BOLT11_INVOICE.upper()
    assert lightning_uri(upper) == f"lightning:{upper}"


@pytest.mark.parametrize(
    "payload",
    [
        "",  # empty
        "lnBC1abc",  # mixed-case bech32 is invalid (BIP-173)
        "lightning:lnbc1abc",  # already a URI, not a bare payload
        "lnbc1 abc",  # space
        "lnbc1?x",  # query character
        "lnbc1@x",  # @
        "xnbc1abc",  # missing the lightning "ln" human-readable prefix
        "ln",  # prefix only, no data
        "naïve1abc",  # non-ASCII
    ],
)
def test_lightning_uri_rejects_bad_payloads(payload: str) -> None:
    with pytest.raises(WalletURIError):
        _ = lightning_uri(payload)


def test_lightning_uri_error_is_a_cuere_error_and_carries_the_value() -> None:
    assert issubclass(WalletURIError, CuereError)
    with pytest.raises(WalletURIError) as exc_info:
        _ = lightning_uri("not a payload")
    assert exc_info.value.value == "not a payload"


def test_lightning_uri_composes_with_optimize_uri() -> None:
    # A lowercase invoice is byte-mode bare, but optimize_uri uppercases the
    # lightning: URI into QR-alphanumeric mode for a smaller code.
    uri = lightning_uri(BOLT11_INVOICE)
    assert scheme_case(uri) is SchemeCase.INSENSITIVE
    assert optimize_uri(uri) == uri.upper()


def test_lightning_uri_optimization_never_grows_the_qr() -> None:
    uri = lightning_uri(BOLT11_INVOICE)
    original = QRMatrix.encode(uri)
    optimized = QRMatrix.encode(optimize_uri(uri))
    assert isinstance(original.version, int)
    assert isinstance(optimized.version, int)
    assert optimized.version <= original.version


def test_lightning_uri_composes_with_render_and_encode() -> None:
    uri = lightning_uri(BOLT11_INVOICE)
    assert isinstance(render(uri), str)
    assert isinstance(QRMatrix.encode(uri).version, int)


@given(st.text(alphabet="0123456789abcdefghijklmnopqrstuvwxyz", min_size=1))
def test_lightning_uri_round_trips_a_bech32_payload(suffix: str) -> None:
    payload = f"ln{suffix}"
    assert lightning_uri(payload) == f"lightning:{payload}"


# --- ethereum_uri / erc20_transfer_uri (EIP-681) --------------------------

# A mixed-case (EIP-55 checksummed) address and an all-lowercase one.
ETH_ADDRESS = "0xfb6916095ca1df60bb79Ce92ce3ea74c37c5d359"
CONTRACT_ADDRESS = "0x89205A3A3b2A69De6Dbf7f01ED13B2108B2c43e7"
RECIPIENT_ADDRESS = "0x8e23ee67d1332ad560396262c48ffbb01f93d052"
ONE_ETH_IN_WEI = 10**18


def test_bare_ethereum_address_has_no_query() -> None:
    assert ethereum_uri(ETH_ADDRESS) == f"ethereum:{ETH_ADDRESS}"


def test_ethereum_value_is_emitted_as_integer_wei() -> None:
    uri = ethereum_uri(ETH_ADDRESS, value=2014000000000000000)
    assert uri == f"ethereum:{ETH_ADDRESS}?value=2014000000000000000"


def test_ethereum_checksum_case_is_preserved_verbatim() -> None:
    # The mixed-case address carries an EIP-55 checksum; it must survive intact
    # (verbatim, not lower/upper-cased) even alongside a query string.
    assert any(char.isupper() for char in ETH_ADDRESS)  # the fixture is genuinely mixed-case
    assert ethereum_uri(ETH_ADDRESS, value=1) == f"ethereum:{ETH_ADDRESS}?value=1"


def test_ethereum_chain_id_precedes_the_query() -> None:
    uri = ethereum_uri(ETH_ADDRESS, value=1, chain_id=1)
    assert uri == f"ethereum:{ETH_ADDRESS}@1?value=1"


def test_ethereum_gas_params_in_fixed_order() -> None:
    uri = ethereum_uri(ETH_ADDRESS, value=1, gas_limit=21000, gas_price=2000000000)
    assert uri == f"ethereum:{ETH_ADDRESS}?value=1&gasLimit=21000&gasPrice=2000000000"


def test_ethereum_chain_id_with_no_query() -> None:
    assert ethereum_uri(ETH_ADDRESS, chain_id=137) == f"ethereum:{ETH_ADDRESS}@137"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (ONE_ETH_IN_WEI, "1000000000000000000"),  # int
        ("1000000000000000000", "1000000000000000000"),  # base-10 str
        (Decimal("1000000000000000000"), "1000000000000000000"),  # Decimal
        (Decimal("1E+18"), "1000000000000000000"),  # integral, sci-notation Decimal
        (1, "1"),  # one wei, the smallest unit
        (0, "0"),  # 0 is a valid uint256 (EIP-681 imposes no positivity)
        (2**256 - 1, str(2**256 - 1)),  # the uint256 ceiling
    ],
)
def test_ethereum_value_accepts_integer_forms(value: int | Decimal | str, expected: str) -> None:
    assert ethereum_uri(ETH_ADDRESS, value=value) == f"ethereum:{ETH_ADDRESS}?value={expected}"


@pytest.mark.parametrize(
    "address",
    [
        "",
        "fb6916095ca1df60bb79Ce92ce3ea74c37c5d359",  # missing 0x
        "0xfb6916",  # too short
        ETH_ADDRESS + "00",  # too long
        "0xfb6916095ca1df60bb79Ce92ce3ea74c37c5d35g",  # non-hex digit
        "0Xfb6916095ca1df60bb79Ce92ce3ea74c37c5d359",  # capital X prefix
        "ethereum:" + ETH_ADDRESS,  # already a URI, not a bare address
    ],
)
def test_invalid_ethereum_address_is_rejected(address: str) -> None:
    with pytest.raises(WalletURIError):
        _ = ethereum_uri(address)


@pytest.mark.parametrize(
    "value",
    [
        -1,  # negative is outside the uint256 domain
        Decimal("1.5"),  # not a whole number of wei
        "1.5",  # likewise as a string
        "not-a-number",  # unparseable
        Decimal("NaN"),  # not finite
        Decimal("Infinity"),  # not finite
        True,  # bool is an int subtype but never a valid amount
        False,
        2**256,  # one past the uint256 ceiling
    ],
)
def test_invalid_ethereum_value_is_rejected(value: int | Decimal | str) -> None:
    with pytest.raises(WalletURIError):
        _ = ethereum_uri(ETH_ADDRESS, value=value)


@pytest.mark.parametrize("chain_id", [-1, True, 2**256])
def test_invalid_chain_id_is_rejected(chain_id: int) -> None:
    with pytest.raises(WalletURIError):
        _ = ethereum_uri(ETH_ADDRESS, chain_id=chain_id)


def test_erc20_transfer_canonical_example() -> None:
    # The structure of the EIP-681 transfer example: scheme, the /transfer path,
    # and the address=<to>&uint256=<amount> argument keys in that fixed order.
    uri = erc20_transfer_uri(CONTRACT_ADDRESS, to=RECIPIENT_ADDRESS, amount=1)
    assert uri == f"ethereum:{CONTRACT_ADDRESS}/transfer?address={RECIPIENT_ADDRESS}&uint256=1"


def test_erc20_transfer_with_chain_id_and_gas() -> None:
    uri = erc20_transfer_uri(
        CONTRACT_ADDRESS,
        to=RECIPIENT_ADDRESS,
        amount=100,
        chain_id=1,
        gas_limit=60000,
    )
    assert uri == (
        f"ethereum:{CONTRACT_ADDRESS}@1/transfer"
        f"?address={RECIPIENT_ADDRESS}&uint256=100&gasLimit=60000"
    )


def test_erc20_transfer_amount_must_be_a_whole_nonnegative_uint256() -> None:
    # A fractional or negative token amount is rejected; 0 is a valid uint256.
    with pytest.raises(WalletURIError):
        _ = erc20_transfer_uri(CONTRACT_ADDRESS, to=RECIPIENT_ADDRESS, amount=Decimal("1.5"))
    with pytest.raises(WalletURIError):
        _ = erc20_transfer_uri(CONTRACT_ADDRESS, to=RECIPIENT_ADDRESS, amount=-1)
    assert erc20_transfer_uri(CONTRACT_ADDRESS, to=RECIPIENT_ADDRESS, amount=0) == (
        f"ethereum:{CONTRACT_ADDRESS}/transfer?address={RECIPIENT_ADDRESS}&uint256=0"
    )


def test_erc20_transfer_validates_both_addresses() -> None:
    with pytest.raises(WalletURIError):  # bad token
        _ = erc20_transfer_uri("0xnot", to=RECIPIENT_ADDRESS, amount=1)
    with pytest.raises(WalletURIError):  # bad recipient
        _ = erc20_transfer_uri(CONTRACT_ADDRESS, to="0xnot", amount=1)


def test_ethereum_error_is_a_cuere_error_and_carries_the_value() -> None:
    assert issubclass(WalletURIError, CuereError)
    with pytest.raises(WalletURIError) as exc_info:
        _ = ethereum_uri("0xbad")
    assert exc_info.value.value == "0xbad"


def test_optimize_uri_leaves_built_ethereum_uris_untouched() -> None:
    # EIP-55 case is significant: optimize_uri must never alter an ethereum: URI.
    for uri in (
        ethereum_uri(ETH_ADDRESS, value=ONE_ETH_IN_WEI),
        erc20_transfer_uri(CONTRACT_ADDRESS, to=RECIPIENT_ADDRESS, amount=1),
    ):
        assert optimize_uri(uri) == uri


def test_ethereum_uri_composes_with_render_and_encode() -> None:
    uri = ethereum_uri(ETH_ADDRESS, value=ONE_ETH_IN_WEI, chain_id=1)
    assert isinstance(render(uri), str)
    assert isinstance(QRMatrix.encode(uri).version, int)


@given(st.integers(min_value=0, max_value=2**256 - 1))
def test_ethereum_value_round_trips_as_integer_wei(value: int) -> None:
    uri = ethereum_uri(ETH_ADDRESS, value=value)
    assert int(uri.partition("value=")[2]) == value
