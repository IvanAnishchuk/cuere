"""Guard against meson-python's no-globbing gotcha.

Meson only ships files listed in py.install_sources; a new module that is
not added to src/cuere/meson.build silently disappears from wheels.
"""

import re
from pathlib import Path

PACKAGE_DIR = Path(__file__).parent.parent / "src" / "cuere"


def test_meson_sources_match_package_directory() -> None:
    meson = (PACKAGE_DIR / "meson.build").read_text(encoding="utf-8")
    # Only quoted tokens that look like installed files, so unrelated quoted
    # strings (the subdir name, comments, future options) can't break this.
    quoted: list[str] = re.findall(r"'([^']+)'", meson)
    listed = {tok for tok in quoted if tok.endswith(".py") or tok == "py.typed"}
    actual = {
        path.name
        for path in PACKAGE_DIR.iterdir()
        if path.suffix == ".py" or path.name == "py.typed"
    }
    assert listed == actual


def test_version_is_defined_only_in_meson() -> None:
    root = PACKAGE_DIR.parent.parent
    meson = (root / "meson.build").read_text(encoding="utf-8")
    # Allow a PEP 440 pre-release/dev suffix (e.g. 0.1.0rc1) as well as X.Y.Z.
    assert re.search(r"version: '\d+\.\d+\.\d+[a-zA-Z0-9.]*'", meson)
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in pyproject
    assert not re.search(r"(?m)^version\s*=", pyproject)
