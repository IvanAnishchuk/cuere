"""Command-line interface: ``cuere [DATA]``."""

import sys
from pathlib import Path
from typing import Annotated

import typer

from cuere import __version__
from cuere.errors import CuereError
from cuere.matrix import ECLevel
from cuere.output import save
from cuere.render import DEFAULT_SCALE, RenderMode
from cuere.terminal import show
from cuere.wallet import optimize_uri

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})

# --dark/--light color the terminal ANSI rendering only; the file/bytes export
# path (save()) has no color knob, so reject the combination rather than silently
# writing a default-colored file.
_COLOR_OUTPUT_ONLY = "--dark / --light apply to terminal output only, not --output"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"cuere {__version__}")
        raise typer.Exit


@app.command()
def main(
    data: Annotated[
        str, typer.Argument(help="Data to encode; '-' (the default) reads from stdin.")
    ] = "-",
    input_file: Annotated[
        Path | None,
        typer.Option("--input", help="Read the payload from this file instead of DATA/stdin."),
    ] = None,
    mode: Annotated[
        RenderMode, typer.Option("--mode", "-m", help="Rendering mode.")
    ] = RenderMode.HALF,
    invert: Annotated[
        bool, typer.Option("--invert", "-i", help="Flip dark and light modules.")
    ] = False,
    border: Annotated[
        int, typer.Option(help="Quiet-zone width in modules (the spec wants >= 4).")
    ] = 4,
    error: Annotated[
        ECLevel, typer.Option("--error", "-e", help="Error-correction level.")
    ] = ECLevel.L,
    micro: Annotated[
        bool, typer.Option("--micro", help="Use a compact Micro QR code (small payloads only).")
    ] = False,
    boost_error: Annotated[
        bool,
        typer.Option("--boost-error", help="Raise EC level when there is spare capacity."),
    ] = False,
    optimize: Annotated[
        bool,
        typer.Option("--optimize-uri", help="Uppercase a lowercase URI when that shrinks the QR."),
    ] = False,
    check_width: Annotated[
        bool,
        typer.Option(
            "--check-width/--no-check-width",
            help="Fail when the code is wider than the terminal.",
        ),
    ] = True,
    force: Annotated[
        bool, typer.Option("--force", help="Emit ANSI colors even when NO_COLOR/not a tty.")
    ] = False,
    dark: Annotated[
        str | None,
        typer.Option(
            "--dark",
            help="ANSI dark-module color: a name, 0-255 index, #hex, or r,g,b. Needs --mode ansi.",
        ),
    ] = None,
    light: Annotated[
        str | None,
        typer.Option(
            "--light",
            help="ANSI light-ground color: a name, 0-255 index, #hex, or r,g,b. Needs --mode ansi.",
        ),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            metavar="FORMAT[:PATH]",
            help=(
                "Write FORMAT (text/svg/png) to PATH instead of the terminal;"
                + " PATH '-' or omitted means stdout. PNG needs the cuere[image] extra."
            ),
        ),
    ] = None,
    scale: Annotated[
        int, typer.Option("--scale", help="Pixels per module for svg/png output.")
    ] = DEFAULT_SCALE,
    _version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = False,
) -> None:
    """Render DATA as a QR code in the terminal."""
    if output is not None and (dark is not None or light is not None):
        # Colors apply to terminal output only; fail fast (before reading input)
        # with the same clean error/exit code as a color used on a non-ANSI mode.
        typer.echo(f"error: {_COLOR_OUTPUT_ONLY}", err=True)
        raise typer.Exit(code=1)
    try:
        if input_file is not None:
            payload = input_file.read_text(encoding="utf-8").rstrip("\r\n")
        elif data == "-":
            payload = sys.stdin.read().rstrip("\r\n")
        else:
            payload = data
        if optimize:
            payload = optimize_uri(payload)
        if output is None:
            show(
                payload,
                mode=mode,
                invert=invert,
                border=border,
                error=error,
                micro=micro,
                boost_error=boost_error,
                on_too_wide="error" if check_width else "render",
                force=force,
                dark=dark,
                light=light,
            )
        else:
            # FORMAT[:PATH]; a missing path or '-' means stdout. save() owns the
            # render-and-write so the CLI and library share one code path.
            fmt, _, dest = output.partition(":")
            target = sys.stdout.buffer if dest in ("", "-") else dest
            save(
                payload,
                target,
                format=fmt,
                mode=mode,
                invert=invert,
                scale=scale,
                border=border,
                error=error,
                micro=micro,
                boost_error=boost_error,
            )
    except (CuereError, OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError (a ValueError, not an OSError) fires when --input or
        # stdin holds non-UTF-8 bytes; surface it as a clean error, not a traceback.
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
