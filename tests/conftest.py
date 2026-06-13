"""Shared fixtures and hypothesis profiles."""

from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

import pytest
from hypothesis import settings

if TYPE_CHECKING:
    from collections.abc import Callable

settings.register_profile("ci", max_examples=200)
settings.register_profile("dev", max_examples=50)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


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
