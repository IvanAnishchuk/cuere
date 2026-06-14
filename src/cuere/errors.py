"""Exception hierarchy for cuere."""


class CuereError(Exception):
    """Base class for all cuere errors."""


class EncodingError(CuereError):
    """Raised when data cannot be encoded as a QR code."""


class WalletURIError(CuereError):
    """Raised when arguments to a wallet-URI builder are invalid.

    Carries the offending value; the human-readable reason is built here so
    call sites never pass a message string (keeping the public exception
    contract a pure :class:`CuereError`, never a bare ``ValueError``).
    """

    value: object

    def __init__(self, reason: str, value: object) -> None:
        super().__init__(f"{reason}: {value!r}")
        self.value = value


class WidthError(CuereError):
    """Raised when a rendered QR code does not fit the available width."""

    required: int
    available: int

    def __init__(self, required: int, available: int) -> None:
        super().__init__(f"QR code needs {required} columns but only {available} are available")
        self.required = required
        self.available = available
