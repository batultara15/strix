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


def test_fetched_collections_never_reuse_predictable_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(utils.tempfile, "tempdir", str(tmp_path))
    shared = tmp_path / "strix_api_specs" / "fetched"
    shared.mkdir(parents=True)
    victim = shared / "collection.postman_collection.json"
    victim.write_text("leave this file untouched", encoding="utf-8")
    first = Path(utils.write_fetched_collection({"fake": "one"}, "collection"))
    second = Path(utils.write_fetched_collection({"fake": "two"}, "collection"))
    assert first.parent != second.parent
    assert first.parent.parent == tmp_path
    assert victim.read_text(encoding="utf-8") == "leave this file untouched"


def test_spec_staging_does_not_follow_run_name_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(utils.tempfile, "tempdir", str(tmp_path))
    source = tmp_path / "spec.json"
    source.write_text("{}", encoding="utf-8")
    target = {"type": "api_spec", "details": {"target_spec": str(source)}}
    first = Path(utils.stage_api_specs([target], "../victim")[0]["source_path"])
    second = Path(utils.stage_api_specs([target], "../victim")[0]["source_path"])
    assert first != second
    assert first.parent == tmp_path
    assert (first / "spec.json").read_text(encoding="utf-8") == "{}"


@pytest.mark.parametrize(
    "url",
    [
        "https://TEST_FAKE_TOKEN_DO_NOT_USE@example.test/repo.git",
        "https://user:TEST_FAKE_PASSWORD@example.test/repo.git",
        "https://example.test/repo.git?token=TEST_FAKE_TOKEN_DO_NOT_USE",
        "https://example.test/repo.git#TEST_FAKE_TOKEN_DO_NOT_USE",
    ],
)
def test_clone_rejects_inline_credentials_before_logging_or_subprocess(
    url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    console = Mock()
    run = Mock()
    monkeypatch.setattr(utils, "Console", console)
    monkeypatch.setattr(utils.subprocess, "run", run)
    with pytest.raises(ValueError, match="credential helper") as error:
        utils.clone_repository(url, "run")
    assert "TEST_FAKE" not in str(error.value)
    console.assert_not_called()
    run.assert_not_called()


def test_git_failure_does_not_disclose_remote_diagnostics(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(utils.shutil, "which", lambda _: "git")
    monkeypatch.setattr(utils.tempfile, "tempdir", str(tmp_path))
    failure = utils.subprocess.CalledProcessError(128, ["git"], stderr="TEST_FAKE_REMOTE_SECRET")
    monkeypatch.setattr(utils.subprocess, "run", Mock(side_effect=failure))
    with pytest.raises(ValueError, match="Git exit 128") as error:
        utils.clone_repository("https://example.test/repo.git", "run")
    assert "TEST_FAKE_REMOTE_SECRET" not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize(
    "url", ["git@example.test:org/repo.git", "ssh://git@example.test/repo.git"]
)
def test_clone_preserves_ssh_username_support(
    url: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(utils.shutil, "which", lambda _: "git")
    monkeypatch.setattr(utils.tempfile, "tempdir", str(tmp_path))
    run = Mock()
    monkeypatch.setattr(utils.subprocess, "run", run)
    utils.clone_repository(url, "run")
    assert run.call_args.args[0][3] == url
