"""Tests for the typer CLI."""

import importlib
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cuere import __version__, render, render_bytes
from cuere.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def wide_terminal(fixed_terminal: Callable[[int], None]) -> None:
    fixed_terminal(120)


def test_renders_argument() -> None:
    result = runner.invoke(app, ["HELLO"])
    assert result.exit_code == 0
    assert result.stdout == render("HELLO") + "\n"


def test_reads_stdin_by_default() -> None:
    result = runner.invoke(app, [], input="HELLO\n")
    assert result.exit_code == 0
    assert result.stdout == render("HELLO") + "\n"


def test_mode_block() -> None:
    result = runner.invoke(app, ["HELLO", "--mode", "block"])
    assert result.exit_code == 0
    assert result.stdout == render("HELLO", mode="block") + "\n"


def test_invert_and_border_and_error() -> None:
    result = runner.invoke(app, ["HELLO", "--invert", "--border", "2", "--error", "M"])
    assert result.exit_code == 0
    assert result.stdout == render("HELLO", invert=True, border=2, error="M") + "\n"


def test_optimize_uri_flag() -> None:
    uri = "bitcoin:bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
    result = runner.invoke(app, [uri, "--optimize-uri"])
    assert result.exit_code == 0
    assert result.stdout == render(uri.upper()) + "\n"


def test_ansi_force() -> None:
    result = runner.invoke(app, ["HELLO", "--mode", "ansi", "--force"])
    assert result.exit_code == 0
    assert result.stdout == render("HELLO", mode="ansi") + "\n"


def test_dark_and_light_options() -> None:
    result = runner.invoke(
        app, ["HELLO", "--mode", "ansi", "--force", "--dark", "red", "--light", "white"]
    )
    assert result.exit_code == 0
    assert result.stdout == render("HELLO", mode="ansi", dark="red", light="white") + "\n"


def test_dark_requires_ansi_mode_is_a_clean_error() -> None:
    # Colors are ANSI-only; on the default half mode this is a clean error, not a
    # traceback, and not silently ignored.
    result = runner.invoke(app, ["HELLO", "--dark", "red"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_dark_with_output_is_a_clean_error() -> None:
    # Colors apply to terminal output only; combining with --output is a clean
    # error rather than a silently default-colored file.
    result = runner.invoke(app, ["HELLO", "--mode", "ansi", "--dark", "red", "--output", "text"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_bad_mode_is_a_usage_error() -> None:
    result = runner.invoke(app, ["HELLO", "--mode", "sixel"])
    assert result.exit_code == 2


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"cuere {__version__}"


def test_width_error_exits_nonzero(fixed_terminal: Callable[[int], None]) -> None:
    fixed_terminal(10)
    result = runner.invoke(app, ["HELLO"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_no_check_width_renders_anyway(fixed_terminal: Callable[[int], None]) -> None:
    fixed_terminal(10)
    result = runner.invoke(app, ["HELLO", "--no-check-width"])
    assert result.exit_code == 0
    assert result.stdout == render("HELLO") + "\n"


def test_dunder_main_module_imports() -> None:
    module = importlib.import_module("cuere.__main__")
    assert vars(module)["app"] is app


def test_input_file(tmp_path: Path) -> None:
    payload_file = tmp_path / "payload.txt"
    _ = payload_file.write_text("FROM FILE\n", encoding="utf-8")
    result = runner.invoke(app, ["--input", str(payload_file)])
    assert result.exit_code == 0
    assert result.stdout == render("FROM FILE") + "\n"


def test_input_file_missing() -> None:
    result = runner.invoke(app, ["--input", "/no/such/cuere/file.txt"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_input_file_non_utf8(tmp_path: Path) -> None:
    # A binary / non-UTF-8 file is a clean error, not an uncaught UnicodeDecodeError.
    payload_file = tmp_path / "binary.bin"
    _ = payload_file.write_bytes(b"\xff\xfe\x00not utf-8")
    result = runner.invoke(app, ["--input", str(payload_file)])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_micro_flag() -> None:
    result = runner.invoke(app, ["12345", "--micro"])
    assert result.exit_code == 0
    assert result.stdout == render("12345", micro=True) + "\n"


def test_boost_error_flag() -> None:
    result = runner.invoke(app, ["HELLO", "--boost-error"])
    assert result.exit_code == 0
    assert result.stdout == render("HELLO", boost_error=True) + "\n"


def test_output_svg_to_file(tmp_path: Path) -> None:
    dest = tmp_path / "out.svg"
    result = runner.invoke(app, ["HELLO", "--output", f"svg:{dest}"])
    assert result.exit_code == 0
    assert dest.read_bytes() == render_bytes("HELLO", format="svg")


def test_output_png_to_file_honors_scale(tmp_path: Path) -> None:
    dest = tmp_path / "out.png"
    result = runner.invoke(app, ["HELLO", "-o", f"png:{dest}", "--scale", "3"])
    assert result.exit_code == 0
    assert dest.read_bytes() == render_bytes("HELLO", format="png", scale=3)


def test_output_text_to_stdout() -> None:
    result = runner.invoke(app, ["HELLO", "--output", "text"])
    assert result.exit_code == 0
    assert result.stdout_bytes == (render("HELLO") + "\n").encode("utf-8")


def test_output_png_to_stdout() -> None:
    result = runner.invoke(app, ["HELLO", "--output", "png:-"])
    assert result.exit_code == 0
    assert result.stdout_bytes == render_bytes("HELLO", format="png")


def test_output_unknown_format_is_clean_error() -> None:
    result = runner.invoke(app, ["HELLO", "--output", "jpeg:x.jpeg"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_output_non_positive_scale_is_clean_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["HELLO", "-o", f"png:{tmp_path / 'x.png'}", "--scale", "0"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_output_to_file_bypasses_width_check(
    fixed_terminal: Callable[[int], None], tmp_path: Path
) -> None:
    # File output is not gated by the terminal width that errors the default path.
    fixed_terminal(10)
    dest = tmp_path / "out.svg"
    result = runner.invoke(app, ["HELLO", "--output", f"svg:{dest}"])
    assert result.exit_code == 0
    assert dest.exists()


def test_python_dash_m_entry_point() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "cuere", "HELLO", "--no-check-width"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "▀" in result.stdout
