"""QR encoding layer.

This is the only module that talks to segno; everything else operates on
`QRMatrix`.
"""

import enum
from dataclasses import dataclass, replace
from typing import Self, TypedDict, Unpack

import segno

from cuere.errors import EncodingError


class ECLevel(enum.StrEnum):
    """QR error-correction level.

    `L` is the default everywhere in cuere: codes shown on screens are not
    subject to physical damage, and lower correction means fewer modules, so
    the code fits a terminal (this matches what Claude Code CLI does).

    Example:

    ```python
    from cuere import ECLevel, render

    render("HELLO", error=ECLevel.M)   # more robust, slightly larger code
    ```
    """

    L = "L"
    M = "M"
    Q = "Q"
    H = "H"


@dataclass(frozen=True, slots=True)
class QRMatrix:
    """Immutable QR module matrix with the quiet zone baked in.

    `modules` rows must be rectangular; `True` is a dark module.

    Example:

    ```python
    from cuere import QRMatrix, render

    m = QRMatrix.encode("HELLO")        # build the matrix once
    print(m.version, m.width, m.height)
    print(render(m))                    # render a pre-built matrix
    print(render(m.inverted()))         # dark/light flipped
    ```
    """

    modules: tuple[tuple[bool, ...], ...]
    version: int | str
    border: int

    @classmethod
    def encode(
        cls,
        data: str | bytes,
        *,
        error: ECLevel | str = ECLevel.L,
        border: int = 4,
        micro: bool = False,
        boost_error: bool = False,
    ) -> Self:
        """Encode `data` into a QR matrix.

        `boost_error` is off by default on purpose: segno would otherwise
        silently raise the error-correction level when space allows, growing
        the module count for no benefit on a screen.
        """
        try:
            level = ECLevel(error)
            qr = segno.make(data, error=level.value, micro=micro, boost_error=boost_error)
            modules = tuple(tuple(bool(m) for m in row) for row in qr.matrix_iter(border=border))
        except ValueError as exc:  # DataOverflowError and an invalid border are both ValueErrors
            raise EncodingError(str(exc)) from exc
        return cls(modules=modules, version=qr.version, border=border)

    @property
    def size(self) -> int:
        """Number of rows (== columns for encoded matrices), border included."""
        return len(self.modules)

    @property
    def height(self) -> int:
        """Number of module rows."""
        return len(self.modules)

    @property
    def width(self) -> int:
        """Number of module columns."""
        return len(self.modules[0]) if self.modules else 0

    def inverted(self) -> Self:
        """Return a copy with every module flipped."""
        flipped = tuple(tuple(not m for m in row) for row in self.modules)
        return replace(self, modules=flipped)


type Encodable = str | bytes | QRMatrix
"""Anything the high-level API renders: raw `str`/`bytes`, or a built matrix."""


class EncodeOptions(TypedDict, total=False):
    """Encoding keywords the high-level API forwards to `QRMatrix.encode`.

    Declared once and spread via `**opts: Unpack[EncodeOptions]` so the
    option set and its defaults live in a single place (`QRMatrix.encode`).
    """

    error: ECLevel | str
    border: int
    micro: bool
    boost_error: bool


def coerce(data: Encodable, **options: Unpack[EncodeOptions]) -> QRMatrix:
    """Return `data` as a `QRMatrix`, encoding str/bytes input.

    The encode options (`error`/`border`/`micro`/`boost_error`) apply
    only when `data` is encoded; a pre-built `QRMatrix` is returned
    unchanged.
    """
    if isinstance(data, QRMatrix):
        return data
    return QRMatrix.encode(data, **options)
