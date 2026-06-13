"""Tests for the Rich renderable."""

from __future__ import annotations

import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.segment import Segment

from cuere import render
from cuere.rich import ANSI_STYLE, QRCode


def _console() -> Console:
    return Console(record=True, width=80, legacy_windows=False, force_terminal=False)


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
