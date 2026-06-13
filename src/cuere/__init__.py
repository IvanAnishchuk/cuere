"""cuere — QR codes in your terminal.

Unicode half-block rendering (the way Claude Code CLI draws its
remote-connection codes), a Rich renderable, and helpers for crypto-wallet
URIs.
"""

import importlib.metadata

from cuere.errors import CuereError, EncodingError, WidthError
from cuere.matrix import ECLevel, QRMatrix
from cuere.render import RenderMode, render_height, render_matrix, render_width
from cuere.terminal import fits, render, show
from cuere.wallet import is_qr_alphanumeric, optimize_uri

__all__ = [
    "CuereError",
    "ECLevel",
    "EncodingError",
    "QRMatrix",
    "RenderMode",
    "WidthError",
    "__version__",
    "fits",
    "is_qr_alphanumeric",
    "optimize_uri",
    "render",
    "render_height",
    "render_matrix",
    "render_width",
    "show",
]


def _get_version(dist_name: str) -> str:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+unknown"


__version__ = _get_version("cuere")
