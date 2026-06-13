"""Shared fixtures and hypothesis profiles."""

import os
import shutil
from collections.abc import Callable

import pytest
from hypothesis import Phase, settings

settings.register_profile("ci", max_examples=200)
settings.register_profile("dev", max_examples=50)
# Under mutmut (it sets MUTANT_UNDER_TEST), a failing example already means the
# mutant is caught, so skip the shrink phase: shrinking a failure is pure
# overhead here and can overrun mutmut's per-mutant timeout, turning a clean
# kill into a flaky ⏰ timeout. Detection (generation) is unaffected.
settings.register_profile(
    "mutmut",
    max_examples=50,
    phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.target),
    deadline=None,
)
_under_mutmut = bool(os.environ.get("MUTANT_UNDER_TEST"))
_profile = "mutmut" if _under_mutmut else os.environ.get("HYPOTHESIS_PROFILE", "dev")
settings.load_profile(_profile)


@pytest.fixture
def fixed_terminal(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Pin the terminal size reported to cuere.terminal."""

    def _set(columns: int, lines: int = 50) -> None:
        size = os.terminal_size((columns, lines))

        def _fake_get_terminal_size(_fallback: tuple[int, int] = (80, 24)) -> os.terminal_size:
            return size

        monkeypatch.setattr(shutil, "get_terminal_size", _fake_get_terminal_size)

    return _set


@pytest.fixture
def no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")


@pytest.fixture
def color_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
