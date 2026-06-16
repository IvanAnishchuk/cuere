"""Rich renderable for QR codes.

Example:

```python
from rich.console import Console
from cuere.rich import QRCode

Console().print(QRCode("wc:..."), justify="center")
```
"""

from typing import Unpack

from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style

from cuere.matrix import Encodable, EncodeOptions, QRMatrix, coerce
from cuere.render import (
    Color,
    RenderMode,
    check_color_mode,
    coerce_mode,
    render_matrix,
    render_width,
    resolve_pair,
)

# Same polarity as render.ANSI_PREFIX, expressed as a Style so Rich owns the
# SGR emission (and can strip it for export_text, files, etc.). Built from the
# render defaults via resolve_pair so it can never drift from the SGR text path.
_DEFAULT_FG, _DEFAULT_BG = resolve_pair(None, None)


def _rich_color(resolved: int | tuple[int, int, int]) -> str:
    """Format a resolved color (palette index or rgb triple) as a Rich color string.

    Consumes `resolve_pair`'s output so a Rich-rendered code
    uses exactly the colors the SGR text path would: a palette index becomes
    `"color(N)"` and a truecolor triple becomes `"rgb(r,g,b)"`.
    """
    if isinstance(resolved, int):
        return f"color({resolved})"
    red, green, blue = resolved
    return f"rgb({red},{green},{blue})"


ANSI_STYLE = Style(color=_rich_color(_DEFAULT_FG), bgcolor=_rich_color(_DEFAULT_BG))


class QRCode:
    """A QR code that can be printed, centered, or framed by Rich.

    Example:

    ```python
    from rich.console import Console
    from rich.panel import Panel
    from cuere.rich import QRCode

    Console().print(Panel(QRCode("bitcoin:BC1Q..."), title="scan to pay"))
    ```
    """

    matrix: QRMatrix
    mode: RenderMode
    invert: bool
    dark: Color | None
    light: Color | None

    def __init__(
        self,
        data: Encodable,
        *,
        mode: RenderMode | str = RenderMode.HALF,
        invert: bool = False,
        dark: Color | None = None,
        light: Color | None = None,
        **options: Unpack[EncodeOptions],
    ) -> None:
        self.matrix = coerce(data, **options)
        self.mode = coerce_mode(mode)
        self.invert = invert
        self.dark = dark
        self.light = light
        # Same contract as the text renderer: colors apply only to ANSI mode.
        check_color_mode(self.mode, dark, light)
        if self.mode is RenderMode.ANSI:
            # Validate the colors now so a bad one fails at construction (like
            # render/show), not deep inside a later Console.print.
            _ = resolve_pair(dark, light)

    def _text_mode(self) -> RenderMode:
        # ANSI mode delegates color to Rich, so the glyphs are HALF's.
        return RenderMode.HALF if self.mode is RenderMode.ANSI else self.mode

    def _style(self) -> Style | None:
        # Non-ANSI modes inherit the terminal's colors (no Style); ANSI without
        # custom colors keeps the shared ANSI_STYLE (identity), so its segments
        # stay interchangeable with the default code.
        if self.mode is not RenderMode.ANSI:
            return None
        if self.dark is None and self.light is None:
            return ANSI_STYLE
        fg, bg = resolve_pair(self.dark, self.light)
        return Style(color=_rich_color(fg), bgcolor=_rich_color(bg))

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        style = self._style()
        text = render_matrix(self.matrix, mode=self._text_mode(), invert=self.invert)
        for line in text.split("\n"):
            yield Segment(line, style)
            yield Segment.line()

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        width = render_width(self.matrix, self._text_mode())
        return Measurement(width, width)
