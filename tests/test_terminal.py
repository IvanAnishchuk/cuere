"""Tests for the high-level render/show/fits API."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, cast, override

import pytest

from cuere import CuereError, QRMatrix, RenderMode, WidthError, fits, render, show

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

HELLO_COLS = 29  # version 1 + 4-module border
HELLO_ROWS = 15  # ceil(29 / 2) half-block rows


class _FakeTty(io.StringIO):
    @override
    def isatty(self) -> bool:
        return True


class _WriteOnly:
    """A stream without isatty, like some wrapped file objects."""

    text: str

    def __init__(self) -> None:
        self.text = ""

    def write(self, data: str) -> int:
        self.text += data
        return len(data)


def test_render_accepts_str_bytes_and_matrix() -> None:
    matrix = QRMatrix.encode("HELLO")
    from_matrix = render(matrix)
    assert render("HELLO") == from_matrix
    assert render(b"HELLO") == from_matrix


def test_render_accepts_mode_strings() -> None:
    assert render("HELLO", mode="block") == render("HELLO", mode=RenderMode.BLOCK)


def test_unknown_mode_raises_cuere_error() -> None:
    with pytest.raises(CuereError):
        _ = render("HELLO", mode="sixel")


def test_show_writes_render_plus_newline() -> None:
    out = io.StringIO()
    show("HELLO", out=out, width=100)
    assert out.getvalue() == render("HELLO") + "\n"


def test_show_default_stream_is_stdout(
    capsys: pytest.CaptureFixture[str], fixed_terminal: Callable[[int], None]
) -> None:
    fixed_terminal(100)
    show("HELLO")
    assert capsys.readouterr().out == render("HELLO") + "\n"


def test_show_raises_width_error_with_fields() -> None:
    out = io.StringIO()
    with pytest.raises(WidthError) as excinfo:
        show("HELLO", out=out, width=10)
    assert excinfo.value.required == HELLO_COLS
    assert excinfo.value.available == 10
    assert out.getvalue() == ""


def test_show_warn_mode_renders_anyway() -> None:
    out = io.StringIO()
    with pytest.warns(UserWarning, match="probably not scan"):
        show("HELLO", out=out, width=10, on_too_wide="warn")
    assert out.getvalue() == render("HELLO") + "\n"


def test_show_render_mode_is_silent() -> None:
    out = io.StringIO()
    show("HELLO", out=out, width=10, on_too_wide="render")
    assert out.getvalue() == render("HELLO") + "\n"


def test_show_uses_terminal_size_when_width_omitted(
    fixed_terminal: Callable[[int], None],
) -> None:
    fixed_terminal(10)
    with pytest.raises(WidthError):
        show("HELLO", out=io.StringIO())


def test_fits(fixed_terminal: Callable[..., None]) -> None:
    assert fits("HELLO", width=HELLO_COLS, height=HELLO_ROWS)
    assert not fits("HELLO", width=HELLO_COLS - 1, height=HELLO_ROWS)  # too wide
    assert not fits("HELLO", width=HELLO_COLS, height=HELLO_ROWS - 1)  # too tall
    assert not fits("HELLO", mode="block", width=HELLO_COLS, height=HELLO_ROWS)
    fixed_terminal(HELLO_COLS, HELLO_ROWS)
    assert fits("HELLO")
    fixed_terminal(HELLO_COLS - 1, HELLO_ROWS)
    assert not fits("HELLO")
    fixed_terminal(HELLO_COLS, HELLO_ROWS - 1)
    assert not fits("HELLO")


def test_render_micro_qr() -> None:
    out = render("12345", micro=True)
    assert out
    assert out != render("12345")


def test_render_boost_error() -> None:
    assert render("HI", boost_error=True) != render("HI")


# ── ANSI fallback guard ──────────────────────────────────────────


@pytest.mark.usefixtures("color_ok")
def test_ansi_downgrades_on_non_tty() -> None:
    out = io.StringIO()
    show("HELLO", mode="ansi", out=out, width=100)
    assert "\x1b[" not in out.getvalue()
    assert out.getvalue() == render("HELLO") + "\n"


@pytest.mark.usefixtures("color_ok")
def test_ansi_kept_on_tty() -> None:
    out = _FakeTty()
    show("HELLO", mode="ansi", out=out, width=100)
    assert out.getvalue() == render("HELLO", mode="ansi") + "\n"


@pytest.mark.usefixtures("no_color")
def test_ansi_downgrades_under_no_color() -> None:
    out = _FakeTty()
    show("HELLO", mode="ansi", out=out, width=100)
    assert "\x1b[" not in out.getvalue()


def test_ansi_downgrades_when_no_color_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    # Presence of NO_COLOR disables color even when the value is empty.
    monkeypatch.setenv("NO_COLOR", "")
    out = _FakeTty()
    show("HELLO", mode="ansi", out=out, width=100)
    assert "\x1b[" not in out.getvalue()


@pytest.mark.usefixtures("no_color")
def test_ansi_force_overrides_guards() -> None:
    out = io.StringIO()
    show("HELLO", mode="ansi", out=out, width=100, force=True)
    assert out.getvalue() == render("HELLO", mode="ansi") + "\n"


@pytest.mark.usefixtures("color_ok")
def test_ansi_downgrades_on_stream_without_isatty() -> None:
    out = _WriteOnly()
    show("HELLO", mode="ansi", out=cast("IO[str]", cast("object", out)), width=100)
    assert "\x1b[" not in out.text


def test_invert_passthrough() -> None:
    out = io.StringIO()
    show("HELLO", out=out, width=100, invert=True)
    assert out.getvalue() == render("HELLO", invert=True) + "\n"
