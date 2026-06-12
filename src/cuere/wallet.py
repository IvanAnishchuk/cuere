"""Helpers for QR-encoding crypto-wallet URIs.

QR alphanumeric mode covers only ``0-9 A-Z space $%*+-./:`` but produces a
much smaller code than byte mode. BIP-173 (bech32) and the BIP-21 scheme are
case-insensitive, so a fully lowercase ``bitcoin:bc1...`` URI can be
uppercased wholesale to qualify. URIs with query strings contain ``?``/``=``/
``&``, which alphanumeric mode cannot represent, so they pass through
unchanged — as does anything mixed-case (the case may be significant, e.g.
EIP-55 checksums or base58 addresses).
"""

from __future__ import annotations

_QR_ALPHANUMERIC = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:")


def is_qr_alphanumeric(data: str) -> bool:
    """Whether ``data`` is non-empty and encodable in QR alphanumeric mode."""
    return bool(data) and all(char in _QR_ALPHANUMERIC for char in data)


def optimize_uri(uri: str) -> str:
    """Uppercase ``uri`` when that provably shrinks its QR code.

    The transformation is applied only when ``uri`` is entirely lowercase
    (so uppercasing cannot destroy significant case) and the uppercased form
    is fully QR-alphanumeric. Idempotent; returns the input unchanged in
    every other case.
    """
    if uri != uri.lower():
        return uri
    upper = uri.upper()
    if not is_qr_alphanumeric(upper):
        return uri
    return upper
