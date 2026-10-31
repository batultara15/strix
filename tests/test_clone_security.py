"""Host path boundaries for repository targets."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from strix.interface import utils


@pytest.mark.parametrize("name", [".", ".."])
def test_special_dot_names_are_not_path_components(name: str) -> None:
    assert utils.sanitize_name(name) == "target"
    assert utils.derive_repo_base_name("https://example.test/...git") == "target"


@pytest.mark.parametrize("name", ["..", ".", "../victim", "a/b", "a\\b", "/victim"])
def test_clone_rejects_unsafe_destination_before_filesystem_work(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    mkdir = Mock()
    monkeypatch.setattr(utils.shutil, "which", lambda _: "git")
    monkeypatch.setattr(utils.tempfile, "mkdtemp", mkdir)
    with pytest.raises(ValueError, match="single safe directory"):
        utils.clone_repository("https://example.test/repo.git", "run", name)
    mkdir.assert_not_called()


def test_clones_use_private_unique_directories_and_end_git_options(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(utils.shutil, "which", lambda _: "git")
    monkeypatch.setattr(utils.tempfile, "tempdir", str(tmp_path))
    delete = Mock(side_effect=AssertionError("must not delete a host path"))
    run = Mock()
    monkeypatch.setattr(utils.shutil, "rmtree", delete)
    monkeypatch.setattr(utils.subprocess, "run", run)
    first = Path(utils.clone_repository("https://example.test/repo.git", "run"))
    second = Path(utils.clone_repository("https://example.test/repo.git", "run"))
    assert first.parent != second.parent
    assert first.parent.parent == tmp_path
    assert run.call_args.args[0][1:3] == ["clone", "--"]
    delete.assert_not_called()
