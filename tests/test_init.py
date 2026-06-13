"""Package-surface tests."""

from __future__ import annotations

import cuere


def test_version_is_resolved() -> None:
    assert cuere.__version__ == cuere._get_version("cuere")  # pyright: ignore[reportPrivateUsage]
    assert cuere.__version__ != "0.0.0+unknown"


def test_version_falls_back_when_not_installed() -> None:
    missing = "definitely-not-an-installed-distribution"
    assert cuere._get_version(missing) == "0.0.0+unknown"  # pyright: ignore[reportPrivateUsage]


def test_all_exports_exist() -> None:
    for name in cuere.__all__:
        assert hasattr(cuere, name)
