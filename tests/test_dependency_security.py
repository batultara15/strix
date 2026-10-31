"""Regression guard for advisory-affected resolved and installed versions."""

import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest
from packaging.version import Version


MINIMUMS = {"litellm": "1.101.3"}


@pytest.mark.parametrize(("name", "minimum"), MINIMUMS.items())
def test_patched_dependency_is_locked_and_installed(name: str, minimum: str) -> None:
    lock = tomllib.loads((Path(__file__).parents[1] / "uv.lock").read_text(encoding="utf-8"))
    locked = next(package["version"] for package in lock["package"] if package["name"] == name)
    assert Version(locked) >= Version(minimum)
    assert Version(version(name)) >= Version(minimum)
