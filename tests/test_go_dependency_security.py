"""Guard the TUI module against the audited vulnerable dependency ranges."""

import re
from pathlib import Path

from packaging.version import Version


def test_tui_uses_patched_windows_syscalls() -> None:
    module = (Path(__file__).parents[1] / "strix/interface/tui/go.mod").read_text()
    match = re.search(r"golang.org/x/sys v([0-9.]+)", module)
    assert match is not None
    assert Version(match[1]) >= Version("0.44.0")


def test_tui_uses_patched_text_tables() -> None:
    module = (Path(__file__).parents[1] / "strix/interface/tui/go.mod").read_text()
    match = re.search(r"golang.org/x/text v([0-9.]+)", module)
    assert match is not None
    assert Version(match[1]) >= Version("0.41.0")
