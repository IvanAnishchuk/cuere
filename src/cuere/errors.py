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


class UnknownFormatError(CuereError):
    """Raised when an output format is unrecognized or cannot be inferred.

    Like the other cuere errors, the human-readable message is composed here
    so call sites pass only structured data (``hint`` is a module constant, not
    a raise-site literal): the offending ``value`` plus a ``hint`` that explains
    what was expected.
    """

    value: object

    def __init__(self, value: object, hint: str) -> None:
        super().__init__(f"{hint}: {value!r}")
        self.value = value


class MissingDependencyError(CuereError):
    """Raised when an output format needs an optional dependency that is absent.

    Carries the ``format`` that was requested and the ``extra`` that provides
    it, so the message always points at the right ``pip install`` incantation.
    """

    format: str
    extra: str

    def __init__(self, fmt: str, extra: str) -> None:
        super().__init__(
            f"{fmt} output requires the optional {extra!r} dependency; install cuere[{extra}]"
        )
        self.format = fmt
        self.extra = extra
