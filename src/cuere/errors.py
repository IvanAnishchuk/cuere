"""Exception hierarchy for cuere."""

from __future__ import annotations


class CuereError(Exception):
    """Base class for all cuere errors."""


class EncodingError(CuereError):
    """Raised when data cannot be encoded as a QR code."""


class WidthError(CuereError):
    """Raised when a rendered QR code does not fit the available width."""

    def __init__(self, required: int, available: int) -> None:
        super().__init__(f"QR code needs {required} columns but only {available} are available")
        self.required = required
        self.available = available
