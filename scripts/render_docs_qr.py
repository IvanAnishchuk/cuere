"""Regenerate the terminal-QR art embedded in the documentation pages.

Each ``<!-- qr: KEY -->`` marker in a doc is followed by a fenced code block
whose body is the live ``cuere.render(...)`` output for that KEY. Running this
script rewrites those blocks so the embedded art always matches the current
encoder and renderer. The opening fence is preserved verbatim, so an art block
opts into the scannable ``line-height: 1`` styling with a ``{ .qr }`` info string
(```` ```text { .qr } ````); see ``docs/stylesheets/qr.css`` and issue #68.

The quiet-zone trailing spaces are significant, so every page touched here is
excluded from the ``trailing-whitespace`` pre-commit hook — see ``ART_PAGES``.

Usage:
    uv run python scripts/render_docs_qr.py           # rewrite docs in place
    uv run python scripts/render_docs_qr.py --check    # fail if stale (CI)
"""

import re
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from cuere import (
    bitcoin_uri,
    erc20_transfer_uri,
    ethereum_uri,
    lightning_uri,
    optimize_uri,
    render,
)

console = Console()
REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

# Pages that embed live QR art, in the order they are checked. The quiet-zone
# trailing spaces of that art are significant, so EVERY page listed here MUST
# also be excluded from the `trailing-whitespace` pre-commit hook in
# `.pre-commit-config.yaml` (the cookbook is excluded as a directory; the
# homepage is excluded as a single file). Keep the two lists in sync.
ART_PAGES: tuple[Path, ...] = (
    *sorted(DOCS.glob("cookbook/*.md")),
    DOCS / "index.md",
)

_BTC_ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
# A 62-char bech32 (taproot) address: long enough that optimize_uri's switch to
# alphanumeric mode drops a whole QR version (byte v4 -> alphanumeric v3).
_TAPROOT_ADDRESS = "bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr"
_ETH_ADDRESS = "0xfb6916095ca1df60bb79Ce92ce3ea74c37c5d359"
_USDC_CONTRACT = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
_RECIPIENT = "0x8e23ee67d1332ad560396262c48ffbb01f93d052"
_LN_INVOICE = "lnbc1pvjluezpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqf"
# Shortened, fabricated placeholder: a real wc: URI carries 32-byte (64 hex)
# values minted by the WalletConnect SDK during the pairing handshake.
_WC_PAIRING = "wc:c9e6f7a1@2?relay-protocol=irn&symKey=0123abcd"
# The homepage hero QR scans to the project's GitHub repo.
_HOME_URL = "https://github.com/IvanAnishchuk/cuere"

# KEY -> the payload whose rendered QR is embedded under ``<!-- qr: KEY -->``.
PAYLOADS: dict[str, str] = {
    "HOME": _HOME_URL,
    "BTC_FULL": bitcoin_uri(
        _BTC_ADDRESS,
        amount=Decimal("0.005"),
        label="Coffee",
        message="Order #1234",
    ),
    "BTC_OPT": optimize_uri(bitcoin_uri(_TAPROOT_ADDRESS)),
    "LN": lightning_uri(_LN_INVOICE),
    "ETH": ethereum_uri(_ETH_ADDRESS, value=10**16, chain_id=1),
    "ERC20": erc20_transfer_uri(_USDC_CONTRACT, to=_RECIPIENT, amount=1_000_000, chain_id=1),
    "WC": _WC_PAIRING,
}

# Tolerate trailing whitespace: these pages are excluded from the
# trailing-whitespace pre-commit hook, so a stray space after the marker must not
# silently skip it.
_MARKER = re.compile(r"^<!-- qr: (?P<key>[A-Z0-9_]+) -->\s*$")
_FENCE = "```"
# Each art fence must carry this class so the scannable CSS applies (issue #68).
_QR_CLASS = ".qr"


class DocsArtError(Exception):
    """A docs page is malformed (a ``qr:`` marker without its fenced block)."""


def _art(key: str) -> list[str]:
    """Render KEY's payload as plain half-block glyph lines (quiet zone intact)."""
    return render(PAYLOADS[key], mode="half").splitlines()


def regenerate(text: str) -> str:
    """Return TEXT with every ``qr:`` marker's fenced block refreshed from cuere."""
    lines = text.split("\n")
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        out.append(line)
        index += 1
        marker = _MARKER.match(line)
        if marker is None:
            continue
        key = marker["key"]
        if key not in PAYLOADS:
            msg = f"unknown qr key {key!r}"
            raise DocsArtError(msg)
        if index >= len(lines) or not lines[index].startswith(_FENCE):
            msg = f"marker qr:{key} is not followed by a fenced block"
            raise DocsArtError(msg)
        # The scannable line-height:1 / quiet-zone CSS (docs/stylesheets/qr.css)
        # only applies to blocks carrying the `{ .qr }` class. The art bytes match
        # the renderer either way, so without this guard a fence that lost `{ .qr }`
        # would render unscannable with a green --check. Fail fast instead.
        if _QR_CLASS not in lines[index]:
            msg = f"marker qr:{key} fence is missing its `{{ .qr }}` class (see qr.css)"
            raise DocsArtError(msg)
        out.append(lines[index])  # opening fence (e.g. ```text { .qr })
        index += 1
        while index < len(lines) and lines[index].strip() != _FENCE:
            index += 1  # discard the stale art body
        if index >= len(lines):
            msg = f"unterminated fenced block after qr:{key}"
            raise DocsArtError(msg)
        out.extend(_art(key))
        out.append(lines[index])  # closing fence
        index += 1
    return "\n".join(out)


def _report(*, check: bool, stale: list[str]) -> None:
    if not stale:
        console.print("[green]docs QR art is up to date[/]")
        return
    names = ", ".join(stale)
    if check:
        console.print(f"[red]stale[/] docs QR art — run scripts/render_docs_qr.py: {names}")
        raise typer.Exit(1)
    console.print(f"[green]regenerated[/] QR art in: {names}")


def main(
    *,
    check: Annotated[
        bool,
        typer.Option("--check", help="Exit non-zero if any page would change."),
    ] = False,
) -> None:
    """Rewrite (or, with --check, verify) the QR art embedded in the docs."""
    stale: list[str] = []
    for path in ART_PAGES:
        original = path.read_text(encoding="utf-8")
        try:
            updated = regenerate(original)
        except DocsArtError as exc:
            console.print(f"[red]error[/] {path.name}: {exc}")
            raise typer.Exit(1) from exc
        if updated == original:
            continue
        stale.append(path.name)
        if not check:
            _ = path.write_text(updated, encoding="utf-8")
    _report(check=check, stale=stale)


if __name__ == "__main__":
    typer.run(main)
