"""Command-line interface: ``cuere [DATA]``."""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from cuere import __version__
from cuere.errors import CuereError
from cuere.matrix import ECLevel
from cuere.render import RenderMode
from cuere.terminal import show
from cuere.wallet import optimize_uri

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"cuere {__version__}")
        raise typer.Exit


@app.command()
def main(
    data: Annotated[
        str, typer.Argument(help="Data to encode; '-' (the default) reads from stdin.")
    ] = "-",
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
    _version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = False,
) -> None:
    """Render DATA as a QR code in the terminal."""
    payload = sys.stdin.read().rstrip("\r\n") if data == "-" else data
    if optimize:
        payload = optimize_uri(payload)
    try:
        show(
            payload,
            mode=mode,
            invert=invert,
            border=border,
            error=error,
            on_too_wide="error" if check_width else "render",
            force=force,
        )
    except CuereError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
