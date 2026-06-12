"""Package-surface tests."""

from __future__ import annotations

import cuere
from cuere import _get_version  # pyright: ignore[reportPrivateUsage]


def test_version_is_resolved() -> None:
    assert cuere.__version__ == _get_version("cuere")
    assert cuere.__version__ != "0.0.0+unknown"


def test_version_falls_back_when_not_installed() -> None:
    assert _get_version("definitely-not-an-installed-distribution") == "0.0.0+unknown"


def test_all_exports_exist() -> None:
    for name in cuere.__all__:
        assert hasattr(cuere, name)
