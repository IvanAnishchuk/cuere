"""Helpers for QR-encoding crypto-wallet URIs.

QR alphanumeric mode covers only ``0-9 A-Z space $%*+-./:`` but produces a
much smaller code than byte mode. bech32 payloads (BIP-173) and their URI
schemes are case-insensitive, so a fully lowercase ``bitcoin:bc1...`` or
``lightning:lnbc...`` URI can be uppercased wholesale to qualify. The
transformation is restricted to those known case-insensitive schemes: it is
never applied to schemes whose case is significant (e.g. ``ethereum:`` with
EIP-55 checksums), to mixed-case URIs, or to URIs whose uppercased form is not
QR-alphanumeric (e.g. anything with a ``?...`` query string).
"""

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from cuere.errors import WalletURIError

_QR_ALPHANUMERIC = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:")

# Schemes whose payloads are case-insensitive (bech32), so uppercasing the
# whole URI is lossless. Deliberately excludes ethereum: and arbitrary schemes.
_CASE_INSENSITIVE_SCHEMES = frozenset({"bitcoin", "lightning"})

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


def optimize_uri(uri: str) -> str:
    """Uppercase a bech32-scheme URI when that provably shrinks its QR code.

    Applied only when **all** of these hold: the scheme is known
    case-insensitive (``bitcoin:`` or ``lightning:``), the URI is already
    entirely lowercase (so uppercasing cannot destroy significant case), and
    the uppercased form is fully QR-alphanumeric. Idempotent; returns the
    input unchanged in every other case.
    """
    scheme, sep, _ = uri.partition(":")
    if not sep or scheme.lower() not in _CASE_INSENSITIVE_SCHEMES:
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
