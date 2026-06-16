"""The QR art embedded in the docs stays in sync with cuere's renderer.

This runs ``scripts/render_docs_qr.py --check``, which re-renders every
``<!-- qr: KEY -->`` block (cookbook + homepage) and fails if any committed art
has drifted from the current encoder/renderer output. It is the CI-side guard
for that art.
"""

import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "render_docs_qr.py"


def test_embedded_docs_qr_art_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
