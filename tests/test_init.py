"""Package-surface tests."""

import re
from pathlib import Path

import pytest

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


def test_api_reference_documents_public_symbols() -> None:
    """Every public symbol (`cuere.__all__`) appears in the API reference.

    Guards the hand-authored `docs/reference/api.md` mkdocstrings `:::` blocks
    against drift: when `__all__` gains or loses a symbol the reference must
    follow, and `zensical --strict` cannot see that correspondence. The reverse
    direction — a `:::` block whose symbol no longer resolves — is caught by
    `zensical build --strict` in CI. Skipped where the docs tree is absent (the
    wheel / mutmut sandbox).
    """
    api_md = Path(__file__).parent.parent / "docs" / "reference" / "api.md"
    if not api_md.exists():
        pytest.skip("docs/reference/api.md not present in this checkout")
    documented = set(re.findall(r":::\s+cuere\.\w+\.(\w+)", api_md.read_text(encoding="utf-8")))
    undocumented = {name for name in cuere.__all__ if name != "__version__"} - documented
    assert not undocumented, f"missing from docs/reference/api.md: {sorted(undocumented)}"
