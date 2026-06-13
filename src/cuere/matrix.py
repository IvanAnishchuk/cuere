"""QR encoding layer.

This is the only module that talks to segno; everything else operates on
:class:`QRMatrix`.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from typing import Self

import segno

from cuere.errors import EncodingError


class ECLevel(enum.StrEnum):
    """QR error-correction level.

    ``L`` is the default everywhere in cuere: codes shown on screens are not
    subject to physical damage, and lower correction means fewer modules, so
    the code fits a terminal (this matches what Claude Code CLI does).
    """

    L = "L"
    M = "M"
    Q = "Q"
    H = "H"


@dataclass(frozen=True, slots=True)
class QRMatrix:
    """Immutable QR module matrix with the quiet zone baked in.

    ``modules`` rows must be rectangular; ``True`` is a dark module.
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
        """Encode ``data`` into a QR matrix.

        ``boost_error`` is off by default on purpose: segno would otherwise
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


def coerce(
    data: str | bytes | QRMatrix,
    *,
    border: int = 4,
    error: ECLevel | str = ECLevel.L,
) -> QRMatrix:
    """Return ``data`` as a :class:`QRMatrix`, encoding str/bytes input."""
    if isinstance(data, QRMatrix):
        return data
    return QRMatrix.encode(data, error=error, border=border)
