"""Optional POSIX APIs must retain the same behavior on every type-checking host."""

from __future__ import annotations

import sys
from contextlib import nullcontext
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from strix.config import codex
from strix.runtime import session_manager


if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("platform_name", ["linux", "darwin", "win32"])
def test_only_linux_passes_host_ids(platform_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    get_uid, get_gid = Mock(return_value=1234), Mock(return_value=5678)
    monkeypatch.setattr(sys, "platform", platform_name)
    monkeypatch.setattr(session_manager.os, "getuid", get_uid, raising=False)
    monkeypatch.setattr(session_manager.os, "getgid", get_gid, raising=False)
    expected = {"STRIX_HOST_UID": "1234", "STRIX_HOST_GID": "5678"}
    assert session_manager._host_identity_env() == (expected if platform_name == "linux" else {})
    assert get_uid.call_count == get_gid.call_count == int(platform_name == "linux")


@pytest.mark.parametrize("raises", [False, True])
def test_refresh_guard_unlocks_optional_posix_api(
    raises: bool, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    flock = Mock()
    monkeypatch.setitem(sys.modules, "fcntl", SimpleNamespace(flock=flock, LOCK_EX=2, LOCK_UN=8))
    monkeypatch.setattr(codex, "AUTH_PATH", tmp_path / "auth.json")
    with (
        pytest.raises(RuntimeError, match="test failure") if raises else nullcontext(),
        codex._refresh_guard(),
    ):
        assert flock.call_count == 1
        if raises:
            raise RuntimeError("test failure")
    assert [call.args[1] for call in flock.call_args_list] == [2, 8]
    assert flock.call_args_list[0].args[0] == flock.call_args_list[1].args[0]
