"""Regression guard for advisory-affected resolved and installed versions."""

import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest
from packaging.version import Version


MINIMUMS = {
    "litellm": "1.101.3",
    "anyio": "4.14.2",
    "certifi": "2026.10.23",
    "urllib3": "2.8.0",
    "pyjwt": "2.15.0",
    "mcp": "1.30.0",
    "multidict": "6.9.1",
    "filelock": "4.2.1",
}


@pytest.mark.parametrize(("name", "minimum"), MINIMUMS.items())
def test_patched_dependency_is_locked_and_installed(name: str, minimum: str) -> None:
    lock = tomllib.loads((Path(__file__).parents[1] / "uv.lock").read_text(encoding="utf-8"))
    locked = next(package["version"] for package in lock["package"] if package["name"] == name)
    assert Version(locked) >= Version(minimum)
    assert Version(version(name)) >= Version(minimum)
