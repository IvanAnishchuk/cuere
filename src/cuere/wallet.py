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

from __future__ import annotations

_QR_ALPHANUMERIC = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:")

# Schemes whose payloads are case-insensitive (bech32), so uppercasing the
# whole URI is lossless. Deliberately excludes ethereum: and arbitrary schemes.
_CASE_INSENSITIVE_SCHEMES = frozenset({"bitcoin", "lightning"})


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
    scheme = uri.partition(":")[0].lower()
    if scheme not in _CASE_INSENSITIVE_SCHEMES:
        return uri
    if uri != uri.lower():
        return uri
    upper = uri.upper()
    if not is_qr_alphanumeric(upper):
        return uri
    return upper
