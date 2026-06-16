"""Exception hierarchy for cuere."""


class CuereError(Exception):
    """Base class for all cuere errors.

    Catch this to handle any cuere-specific failure in one place.

    ```python
    from cuere import CuereError, render

    try:
        render("x" * 10_000)        # more data than any QR version holds
    except CuereError as exc:
        print(exc)
    ```
    """


class EncodingError(CuereError):
    """Raised when data cannot be encoded as a QR code.

    ```python
    from cuere import EncodingError, render

    try:
        render("x" * 10_000)        # exceeds QR capacity
    except EncodingError:
        ...
    ```
    """


class WalletURIError(CuereError):
    """Raised when arguments to a wallet-URI builder are invalid.

    Carries the offending value; the human-readable reason is built here so
    call sites never pass a message string (keeping the public exception
    contract a pure `CuereError`, never a bare `ValueError`).

    ```python
    from cuere import WalletURIError, bitcoin_uri

    try:
        bitcoin_uri("not an address!")
    except WalletURIError as exc:
        print(exc.value)            # the offending input
    ```
    """

    value: object

    def __init__(self, reason: str, value: object) -> None:
        super().__init__(f"{reason}: {value!r}")
        self.value = value


class ColorError(CuereError):
    """Raised when a color argument is malformed or used where no color applies.

    Carries the offending `value` — the bad color, or the render mode that
    cannot take one (only ANSI mode is colored). The message is composed here so
    call sites pass only a reason constant plus the value, never a raise-site
    string literal (keeping the public exception contract a pure
    `CuereError`, mirroring `WalletURIError`).

    ```python
    from cuere import ColorError, render

    try:
        render("HI", mode="ansi", dark="not-a-color")
    except ColorError:
        ...
    ```
    """

    value: object

    def __init__(self, reason: str, value: object) -> None:
        super().__init__(f"{reason}: {value!r}")
        self.value = value


class WidthError(CuereError):
    """Raised when a rendered QR code does not fit the available width.

    ```python
    from cuere import WidthError, show

    try:
        show("a long payload", width=10)   # narrower than the code
    except WidthError as exc:
        print(exc.required, exc.available)
    ```
    """

    required: int
    available: int

    def __init__(self, required: int, available: int) -> None:
        super().__init__(f"QR code needs {required} columns but only {available} are available")
        self.required = required
        self.available = available


class UnknownFormatError(CuereError):
    """Raised when an output format is unrecognized or cannot be inferred.

    Like the other cuere errors, the human-readable message is composed here
    so call sites pass only structured data (`hint` is a module constant, not
    a raise-site literal): the offending `value` plus a `hint` that explains
    what was expected.

    ```python
    from cuere import UnknownFormatError, save

    try:
        save("HI", "out.bmp")       # unrecognized suffix
    except UnknownFormatError:
        ...
    ```
    """

    value: object

    def __init__(self, value: object, hint: str) -> None:
        super().__init__(f"{hint}: {value!r}")
        self.value = value


class MissingDependencyError(CuereError):
    """Raised when an output format needs an optional dependency that is absent.

    Carries the `format` that was requested and the `extra` that provides
    it, so the message always names the right `cuere[<extra>]` to install.

    ```python
    from cuere import MissingDependencyError, render_bytes

    try:
        render_bytes("HI", format="png")   # without the cuere[image] extra
    except MissingDependencyError as exc:
        print(exc.extra)                   # "image"
    ```
    """

    format: str
    extra: str

    def __init__(self, fmt: str, extra: str) -> None:
        super().__init__(
            f"{fmt} output requires the optional {extra!r} dependency; install cuere[{extra}]"
        )
        self.format = fmt
        self.extra = extra
