"""Tests for the Rich renderable."""

import subprocess
import sys

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style

from cuere import ColorError, render
from cuere.rich import ANSI_STYLE, QRCode


def _console() -> Console:
    return Console(record=True, width=80, legacy_windows=False, force_terminal=False)


def _export(qr: QRCode) -> str:
    console = _console()
    console.print(qr)
    return console.export_text()


def test_export_text_matches_plain_render() -> None:
    console = _console()
    console.print(QRCode("HELLO"))
    assert console.export_text() == render("HELLO") + "\n"


def test_block_mode() -> None:
    console = _console()
    console.print(QRCode("HELLO", mode="block"))
    assert console.export_text() == render("HELLO", mode="block") + "\n"


def test_measure_is_exact() -> None:
    console = _console()
    qr = QRCode("HELLO")
    measurement = qr.__rich_measure__(console, console.options)
    assert measurement.minimum == measurement.maximum == 29


def test_ansi_mode_measures_like_half() -> None:
    console = _console()
    qr = QRCode("HELLO", mode="ansi")
    measurement = qr.__rich_measure__(console, console.options)
    assert measurement.minimum == 29


def test_block_mode_measures_double_width() -> None:
    # BLOCK glyphs are two cells wide, so Rich must measure twice the half width
    # or centering/framing of a block-mode code is off.
    console = _console()
    qr = QRCode("HELLO", mode="block")
    measurement = qr.__rich_measure__(console, console.options)
    assert measurement.minimum == measurement.maximum == 58


def test_init_forwards_encode_options() -> None:
    # Every encode knob the constructor accepts must reach the matrix, matching
    # the functional render() with the same option and changing the output.
    assert _export(QRCode("HELLO", border=0)) == render("HELLO", border=0) + "\n"
    assert _export(QRCode("HELLO", border=0)) != _export(QRCode("HELLO"))

    assert _export(QRCode("HELLO", error="H")) == render("HELLO", error="H") + "\n"
    assert _export(QRCode("HELLO", error="H")) != _export(QRCode("HELLO"))

    assert _export(QRCode("12345", micro=True)) == render("12345", micro=True) + "\n"
    assert _export(QRCode("12345", micro=True)) != _export(QRCode("12345"))

    assert _export(QRCode("HI", boost_error=True)) == render("HI", boost_error=True) + "\n"
    assert _export(QRCode("HI", boost_error=True)) != _export(QRCode("HI"))


def test_console_yields_one_segment_per_row() -> None:
    # One content Segment per rendered row keeps the code rectangular for Rich's
    # layout. A single newline-laden segment would export to identical text yet
    # break measurement/justification, so assert the structure, not just the text.
    console = _console()
    segments = list(QRCode("HELLO").__rich_console__(console, console.options))
    content = [s for s in segments if isinstance(s, Segment) and s.text != "\n"]
    assert len(content) == len(render("HELLO").split("\n"))


def test_ansi_mode_segments_carry_style() -> None:
    console = _console()
    qr = QRCode("HELLO", mode="ansi")
    segments = list(qr.__rich_console__(console, console.options))
    content = [s for s in segments if isinstance(s, Segment) and s.text.strip("\n")]
    assert content
    assert all(s.style is ANSI_STYLE for s in content)


def test_half_mode_segments_have_no_style() -> None:
    console = _console()
    segments = list(QRCode("HELLO").__rich_console__(console, console.options))
    assert all(s.style is None for s in segments if isinstance(s, Segment))


def test_ansi_custom_colors_build_a_matching_style() -> None:
    # A named dark + a truecolor light map to the same Rich color strings the SGR
    # text path resolves to (color(N) for palette, rgb(r,g,b) for truecolor).
    console = _console()
    qr = QRCode("HELLO", mode="ansi", dark="red", light=(0, 17, 34))
    content = [
        s
        for s in qr.__rich_console__(console, console.options)
        if isinstance(s, Segment) and s.text.strip("\n")
    ]
    assert content
    expected = Style(color="color(1)", bgcolor="rgb(0,17,34)")
    assert all(s.style == expected for s in content)
    assert all(s.style is not ANSI_STYLE for s in content)


def test_rich_colors_require_ansi_mode() -> None:
    with pytest.raises(ColorError):
        _ = QRCode("HELLO", dark="red")


def test_rich_validates_colors_eagerly() -> None:
    # A malformed color fails at construction (like render/show), not deep inside
    # a later Console.print.
    with pytest.raises(ColorError):
        _ = QRCode("HELLO", mode="ansi", dark="notacolor")


def test_invert_matches_plain_render() -> None:
    console = _console()
    console.print(QRCode("HELLO", invert=True))
    assert console.export_text() == render("HELLO", invert=True) + "\n"


def test_renders_inside_a_panel() -> None:
    console = _console()
    console.print(Panel(QRCode("HELLO"), title="scan me"))
    out = console.export_text()
    assert "scan me" in out
    assert "▀" in out


def test_importing_cuere_does_not_import_rich_or_typer() -> None:
    code = (
        "import sys; import cuere; "
        "sys.exit(1 if ('rich' in sys.modules or 'typer' in sys.modules) else 0)"
    )
    result = subprocess.run([sys.executable, "-c", code], check=False)
    assert result.returncode == 0
