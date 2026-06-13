"""Rich renderable for QR codes.

Usage::

    from rich.console import Console
    from cuere.rich import QRCode

    Console().print(QRCode("wc:..."), justify="center")
"""

from typing import Unpack

from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style

from cuere.matrix import Encodable, EncodeOptions, QRMatrix, coerce
from cuere.render import ANSI_BG, ANSI_FG, RenderMode, coerce_mode, render_matrix, render_width

# Same polarity as render.ANSI_PREFIX, expressed as a Style so Rich owns the
# SGR emission (and can strip it for export_text, files, etc.).
ANSI_STYLE = Style(color=f"color({ANSI_FG})", bgcolor=f"color({ANSI_BG})")


class QRCode:
    """A QR code that can be printed, centered, or framed by Rich."""

    matrix: QRMatrix
    mode: RenderMode
    invert: bool

    def __init__(
        self,
        data: Encodable,
        *,
        mode: RenderMode | str = RenderMode.HALF,
        invert: bool = False,
        **options: Unpack[EncodeOptions],
    ) -> None:
        self.matrix = coerce(data, **options)
        self.mode = coerce_mode(mode)
        self.invert = invert

    def _text_mode(self) -> RenderMode:
        # ANSI mode delegates color to Rich, so the glyphs are HALF's.
        return RenderMode.HALF if self.mode is RenderMode.ANSI else self.mode

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        style = ANSI_STYLE if self.mode is RenderMode.ANSI else None
        text = render_matrix(self.matrix, mode=self._text_mode(), invert=self.invert)
        for line in text.split("\n"):
            yield Segment(line, style)
            yield Segment.line()

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        width = render_width(self.matrix, self._text_mode())
        return Measurement(width, width)
