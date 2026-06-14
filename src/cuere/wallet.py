"""Helpers for QR-encoding crypto-wallet URIs.

QR alphanumeric mode covers only ``0-9 A-Z space $%*+-./:`` but produces a
much smaller code than byte mode. bech32 payloads (BIP-173) and their URI
schemes are case-insensitive, so a fully lowercase ``bitcoin:bc1...`` or
``lightning:lnbc...`` URI can be uppercased wholesale to qualify. The
transformation is restricted to those known case-insensitive schemes
(:class:`SchemeCase`): it is never applied to schemes whose case is significant
(``ethereum:`` with EIP-55 checksums, ``wc:`` WalletConnect), to mixed-case
URIs, or to URIs whose uppercased form is not QR-alphanumeric (e.g. anything
with a ``?...`` query string). :func:`scheme_case` exposes that classification.

This module also builds payment-request URIs: :func:`bitcoin_uri` (BIP-21),
:func:`lightning_uri` (BOLT11 / LNURL / BOLT12), and the EIP-681
:func:`ethereum_uri` / :func:`erc20_transfer_uri`. The ethereum builders emit
byte-mode, case-significant URIs and must never be passed through
:func:`optimize_uri`. See ``docs/bip-21.md``, ``docs/lightning-uri.md``, and
``docs/eip-681.md``.
"""

import enum
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from cuere.errors import WalletURIError

_QR_ALPHANUMERIC = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:")


class SchemeCase(enum.Enum):
    """How a URI scheme's payload responds to case folding.

    This is what decides whether :func:`optimize_uri` may uppercase a URI to
    reach QR *alphanumeric* mode (a smaller code): only an :attr:`INSENSITIVE`
    scheme is ever folded, the other two are always returned verbatim.
    """

    INSENSITIVE = "insensitive"
    """bech32 payload (BIP-173) — case carries no meaning, so uppercasing the
    whole URI is lossless. ``bitcoin:`` and ``lightning:`` (BOLT11 / LNURL)."""
    SIGNIFICANT = "significant"
    """A scheme cuere knows to be case-significant — folding would corrupt it.
    ``ethereum:`` (EIP-55 checksum case) and ``wc:`` (WalletConnect: a
    case-significant relay protocol, a percent-encoded bridge URL, and an opaque
    pairing key)."""
    UNKNOWN = "unknown"
    """A scheme cuere does not recognize, or a string with no scheme at all.
    Treated like :attr:`SIGNIFICANT` — never folded — because cuere cannot prove
    the transform is lossless."""


# Schemes whose payloads are case-insensitive (bech32): uppercasing the whole
# URI is lossless, so optimize_uri may shrink them to QR-alphanumeric mode.
_CASE_INSENSITIVE_SCHEMES = frozenset({"bitcoin", "lightning"})

# Schemes cuere recognizes as case-significant and therefore never folds. Listed
# explicitly (rather than leaning on the unknown-scheme default) so the intent —
# "we know about ethereum:/wc: and deliberately leave them alone" — is pinned.
_CASE_SIGNIFICANT_SCHEMES = frozenset({"ethereum", "wc"})

# A bitcoin address is base58 (legacy/P2SH) or bech32/bech32m (SegWit/Taproot);
# both alphabets, including the bech32 human-readable prefix and separator, are
# a subset of ASCII alphanumerics. This is a structural check that the address
# can sit unescaped in the URI path, NOT a base58check/bech32 checksum verify.
_BITCOIN_ADDRESS = re.compile(r"[0-9A-Za-z]+")

# Bitcoin has 8 decimal places (1 satoshi = 1e-8 BTC); a finer amount is not
# representable on-chain, so reject it rather than emit a URI no wallet can honor.
_SATOSHI_DECIMALS = 8

# Rejection reasons for WalletURIError. Named constants (not raise-site string
# literals) keep message text out of the call site — ruff TRY003 flags literals.
_ERR_BAD_ADDRESS = "not a valid bitcoin address"
_ERR_AMOUNT_BOOL = "amount must be a number, not a bool"
_ERR_AMOUNT_NAN = "amount is not a number"
_ERR_AMOUNT_NOT_FINITE = "amount must be a finite number"
_ERR_AMOUNT_NOT_POSITIVE = "amount must be positive"
_ERR_AMOUNT_SUB_SATOSHI = "amount is finer than one satoshi"


def is_qr_alphanumeric(data: str) -> bool:
    """Whether ``data`` is non-empty and encodable in QR alphanumeric mode."""
    return bool(data) and all(char in _QR_ALPHANUMERIC for char in data)


def scheme_case(uri: str) -> SchemeCase:
    """Classify ``uri`` by how :func:`optimize_uri` treats its scheme's case.

    The scheme is the text before the first ``:`` (compared case-insensitively,
    per RFC 3986). A string with no ``:`` — hence no scheme — is
    :attr:`SchemeCase.UNKNOWN`. Only an :attr:`SchemeCase.INSENSITIVE` scheme is
    a candidate for optimization; see :func:`optimize_uri`.
    """
    scheme, sep, _ = uri.partition(":")
    if not sep:
        return SchemeCase.UNKNOWN
    scheme = scheme.lower()
    if scheme in _CASE_INSENSITIVE_SCHEMES:
        return SchemeCase.INSENSITIVE
    if scheme in _CASE_SIGNIFICANT_SCHEMES:
        return SchemeCase.SIGNIFICANT
    return SchemeCase.UNKNOWN


def optimize_uri(uri: str) -> str:
    """Uppercase a bech32-scheme URI when that provably shrinks its QR code.

    Applied only when **all** of these hold: the scheme is case-insensitive
    (:attr:`SchemeCase.INSENSITIVE` — ``bitcoin:`` or ``lightning:``), the URI
    is already entirely lowercase (so uppercasing cannot destroy significant
    case), and the uppercased form is fully QR-alphanumeric (so a query string
    or any other non-alphanumeric byte rules it out). Idempotent; returns the
    input unchanged in every other case — including case-significant
    (``ethereum:``, ``wc:``) and unrecognized schemes.
    """
    if scheme_case(uri) is not SchemeCase.INSENSITIVE:
        return uri
    if uri != uri.lower():
        return uri
    upper = uri.upper()
    if not is_qr_alphanumeric(upper):
        return uri
    return upper


def _format_amount(amount: Decimal | int | str) -> str:
    """Render a BIP-21 ``amount`` (in BTC) as a plain decimal string.

    Accepts :class:`~decimal.Decimal`, ``int``, or ``str`` (never ``float`` —
    binary floats can't represent decimal money exactly; and ``bool`` is rejected
    even though it is an ``int``). The value must be a finite, positive number
    with at most satoshi (8-decimal) precision; anything else raises
    :class:`~cuere.errors.WalletURIError`.
    """
    if isinstance(amount, bool):  # bool is an int subtype; True would become "1"
        raise WalletURIError(_ERR_AMOUNT_BOOL, amount)
    try:
        value = Decimal(amount)
    except InvalidOperation as exc:
        raise WalletURIError(_ERR_AMOUNT_NAN, amount) from exc
    if not value.is_finite():
        raise WalletURIError(_ERR_AMOUNT_NOT_FINITE, amount)
    if value <= 0:
        raise WalletURIError(_ERR_AMOUNT_NOT_POSITIVE, amount)
    # format(_, "f") avoids scientific notation (Decimal("1E-7") -> "0.0000001").
    # Strip trailing zeros before counting fractional digits: they carry no
    # precision, so "0.500000000" (= 0.5 BTC) must not read as sub-satoshi.
    text = format(value, "f")
    if len(text.partition(".")[2].rstrip("0")) > _SATOSHI_DECIMALS:
        raise WalletURIError(_ERR_AMOUNT_SUB_SATOSHI, amount)
    return text


def bitcoin_uri(
    address: str,
    *,
    amount: Decimal | int | str | None = None,
    label: str | None = None,
    message: str | None = None,
) -> str:
    """Build a well-formed BIP-21 ``bitcoin:`` payment URI.

    ``address`` is validated structurally (base58 or bech32/bech32m alphabet);
    ``amount`` is a BTC value (see :func:`_format_amount`); ``label`` and
    ``message`` are free text and get percent-encoded. Parameters left as
    ``None`` are omitted; an explicit empty ``label``/``message`` is kept as an
    empty value. Invalid input raises :class:`~cuere.errors.WalletURIError`.

    The result is a plain ``str``: pass it to :func:`optimize_uri` (a bare
    address with no query shrinks to QR-alphanumeric) and then to ``render`` /
    ``show`` to draw the code.
    """
    if not _BITCOIN_ADDRESS.fullmatch(address):
        raise WalletURIError(_ERR_BAD_ADDRESS, address)
    params: list[str] = []
    if amount is not None:
        params.append(f"amount={_format_amount(amount)}")
    if label is not None:
        params.append(f"label={quote(label, safe='')}")
    if message is not None:
        params.append(f"message={quote(message, safe='')}")
    uri = f"bitcoin:{address}"
    if params:
        uri = f"{uri}?{'&'.join(params)}"
    return uri


# --- lightning: (BOLT11 / LNURL / BOLT12) ---------------------------------

# A lightning: payload is a bech32 string (BIP-173) whose human-readable part
# begins "ln" (lnbc/lntb/… invoices, lnurl1…, lno1… offers). bech32 is
# case-insensitive but never MIXED-case, so accept an all-lower or an all-upper
# run. Like _BITCOIN_ADDRESS this is a STRUCTURAL check only — a single-case run
# of ASCII alphanumerics beginning "ln"; the bech32 data charset is a subset of
# that, and the checksum is not verified (that needs the bech32 polynomial, a
# dependency cuere deliberately does not pull in).
_LIGHTNING_PAYLOAD = re.compile(r"ln[0-9a-z]+|LN[0-9A-Z]+")

_ERR_BAD_LIGHTNING = "not a lightning payload (BOLT11 invoice, LNURL, or BOLT12 offer)"


def lightning_uri(payload: str) -> str:
    """Build a ``lightning:`` URI from a bech32 Lightning payload.

    ``payload`` is a BOLT11 invoice (``lnbc…`` / ``lntb…`` / …), an LNURL
    (``lnurl1…``), or a BOLT12 offer (``lno1…``) — any bech32 string whose
    human-readable part begins ``ln``. It is validated **structurally** — a
    single-case run of ASCII alphanumerics beginning ``ln`` (the bech32 charset
    is a subset of that) — but its checksum is not verified, mirroring
    :func:`bitcoin_uri`. An empty string, a mixed-case payload, or one carrying a
    ``:`` / ``@`` / query character raises :class:`~cuere.errors.WalletURIError`.

    The result is a plain ``str``. A lowercase payload composes with
    :func:`optimize_uri`, which uppercases the URI to QR-alphanumeric mode for a
    smaller code (``lightning:`` is :attr:`SchemeCase.INSENSITIVE`); pass the
    result to ``render`` / ``show`` to draw it.
    """
    if not _LIGHTNING_PAYLOAD.fullmatch(payload):
        raise WalletURIError(_ERR_BAD_LIGHTNING, payload)
    return f"lightning:{payload}"


# --- EIP-681 (ethereum: / ERC-20 transfer) --------------------------------

# An ethereum address is "0x" followed by 20 bytes = 40 hex digits. The CASE of
# those hex digits is significant: it carries the optional EIP-55 checksum, so
# the address is kept verbatim and never upper/lower-cased. (That is also why
# optimize_uri excludes the ethereum: scheme — see _CASE_INSENSITIVE_SCHEMES.)
# This is a structural check only, NOT an EIP-55 checksum verification: that
# needs keccak-256, a crypto dependency cuere deliberately does not pull in —
# exactly as _BITCOIN_ADDRESS does not verify a base58check/bech32 checksum.
_ETH_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")

# value (wei), gas price (wei), gas limit, chain id, and an ERC-20 amount are
# all EVM uint256 words; reject anything that would not fit on-chain.
_MAX_UINT256 = 2**256 - 1

# Rejection reasons, kept as named constants (never raise-site string literals)
# so ruff TRY003 stays happy; _reason() composes the field-qualified message.
_ERR_BAD_ETH_ADDRESS = "is not a 0x-prefixed 40-hex-digit ethereum address"
_ERR_UINT_BOOL = "must be an integer, not a bool"
_ERR_UINT_NOT_INTEGER = "must be a whole number"
_ERR_UINT_NEGATIVE = "must be a non-negative integer"
_ERR_UINT_TOO_LARGE = "does not fit in a uint256"


def _reason(field: str, problem: str) -> str:
    """Compose a field-qualified ``WalletURIError`` reason (e.g. ``"value ..."``).

    Built in a helper rather than inlined at the raise site so no message string
    literal is passed to the exception constructor — the pattern ruff TRY003
    enforces (see :class:`~cuere.errors.WalletURIError`).
    """
    return f"{field} {problem}"


def _coerce_uint256(value: int | Decimal | str, field: str) -> int:
    """Validate ``value`` as an EVM ``uint256`` and return it as ``int``.

    Accepts :class:`int`, a base-10 :class:`str`, or an integral
    :class:`~decimal.Decimal` (``bool`` is rejected even though it is an ``int``;
    a non-integral, non-finite, negative, or out-of-uint256-range value is
    rejected too). The accepted range is the full ``uint256`` domain
    ``0 … 2**256 - 1`` — ``0`` is valid (it is the EVM word's natural default),
    unlike a BIP-21 ``amount`` which must be positive. ``field`` names the
    offending parameter for the message. Raises
    :class:`~cuere.errors.WalletURIError` on any failure.
    """
    if isinstance(value, bool):  # bool is an int subtype; True would become 1
        raise WalletURIError(_reason(field, _ERR_UINT_BOOL), value)
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise WalletURIError(_reason(field, _ERR_UINT_NOT_INTEGER), value) from exc
    if not number.is_finite() or number != number.to_integral_value():
        raise WalletURIError(_reason(field, _ERR_UINT_NOT_INTEGER), value)
    integer = int(number)
    if integer < 0:
        raise WalletURIError(_reason(field, _ERR_UINT_NEGATIVE), value)
    if integer > _MAX_UINT256:
        raise WalletURIError(_reason(field, _ERR_UINT_TOO_LARGE), value)
    return integer


def _eth_address(address: str, field: str) -> str:
    """Return ``address`` unchanged if it is a structurally valid 0x address.

    Case is preserved verbatim (it carries the EIP-55 checksum when mixed-case;
    an all-lower/all-upper address simply has no checksum). Raises
    :class:`~cuere.errors.WalletURIError` otherwise.
    """
    if not _ETH_ADDRESS.fullmatch(address):
        raise WalletURIError(_reason(field, _ERR_BAD_ETH_ADDRESS), address)
    return address


def _chain_and_gas(
    chain_id: int | None,
    gas_limit: int | None,
    gas_price: int | Decimal | str | None,
) -> tuple[str, list[str]]:
    """Build the ``@<chain_id>`` suffix and the ``gasLimit``/``gasPrice`` params.

    Shared by both EIP-681 builders: ``chain_id`` (if given) becomes the
    ``@<chain_id>`` that sits between the address and the path/query, and the
    gas parameters are appended (in EIP-681 order) to the query.
    """
    suffix = f"@{_coerce_uint256(chain_id, 'chain_id')}" if chain_id is not None else ""
    params: list[str] = []
    if gas_limit is not None:
        params.append(f"gasLimit={_coerce_uint256(gas_limit, 'gas_limit')}")
    if gas_price is not None:
        params.append(f"gasPrice={_coerce_uint256(gas_price, 'gas_price')}")
    return suffix, params


def ethereum_uri(
    address: str,
    *,
    value: int | Decimal | str | None = None,
    chain_id: int | None = None,
    gas_limit: int | None = None,
    gas_price: int | Decimal | str | None = None,
) -> str:
    """Build an EIP-681 ``ethereum:`` native-payment URI.

    ``address`` is the recipient, validated structurally as ``0x`` + 40 hex
    digits with its case preserved (it carries the EIP-55 checksum when
    mixed-case). ``value`` is the amount in **wei** (1 ETH = 10\\ :sup:`18` wei),
    a non-negative integer ``uint256``; ``gas_price`` is likewise in wei and
    ``gas_limit`` is a gas-unit count.
    ``chain_id`` (EIP-155, e.g. ``1`` for mainnet) is emitted as ``@<chain_id>``.
    Parameters left as ``None`` are omitted. Invalid input raises
    :class:`~cuere.errors.WalletURIError`.

    The result is a plain ``str`` to pass to ``render`` / ``show``. Do **not**
    run it through :func:`optimize_uri`: the EIP-55 checksum is case-significant,
    so uppercasing would corrupt the address (``optimize_uri`` already refuses
    the ``ethereum:`` scheme for this reason).
    """
    target = _eth_address(address, "address")
    suffix, params = _chain_and_gas(chain_id, gas_limit, gas_price)
    query: list[str] = []
    if value is not None:
        query.append(f"value={_coerce_uint256(value, 'value')}")
    query.extend(params)
    uri = f"ethereum:{target}{suffix}"
    if query:
        uri = f"{uri}?{'&'.join(query)}"
    return uri


def erc20_transfer_uri(
    token: str,
    *,
    to: str,
    amount: int | Decimal | str,
    chain_id: int | None = None,
    gas_limit: int | None = None,
    gas_price: int | Decimal | str | None = None,
) -> str:
    """Build an EIP-681 ERC-20 ``transfer`` URI: ``ethereum:<token>/transfer?…``.

    Encodes a call to the token's ``transfer(address,uint256)`` function.
    ``token`` is the ERC-20 contract address and ``to`` the recipient, both
    validated as ``0x`` + 40 hex digits with case preserved. ``amount`` is a
    non-negative integer in the token's **base units** (its own ``decimals`` —
    which this library cannot know — so no scaling is applied); it is emitted as
    the ``uint256`` argument. ``chain_id`` / ``gas_limit`` / ``gas_price`` behave as
    in :func:`ethereum_uri`. Invalid input raises
    :class:`~cuere.errors.WalletURIError`.

    As with :func:`ethereum_uri`, never pass the result to :func:`optimize_uri`.
    """
    target = _eth_address(token, "token")
    recipient = _eth_address(to, "to")
    suffix, params = _chain_and_gas(chain_id, gas_limit, gas_price)
    query = [f"address={recipient}", f"uint256={_coerce_uint256(amount, 'amount')}", *params]
    return f"ethereum:{target}{suffix}/transfer?{'&'.join(query)}"
