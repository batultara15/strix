"""Opt-in checks against the real sandbox image, not source-text assertions."""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import tarfile
from typing import TYPE_CHECKING

import pytest

from containers import install_dirsearch


if TYPE_CHECKING:
    from pathlib import Path


IMAGE = os.environ.get("STRIX_SECURITY_IMAGE", "")
requires_image = pytest.mark.skipif(not IMAGE, reason="set STRIX_SECURITY_IMAGE for image checks")


def image_command(entrypoint: str, *arguments: str) -> str:
    docker = shutil.which("docker")
    assert docker is not None, "Docker CLI required for opted-in image checks"
    result = subprocess.run(  # noqa: S603
        [docker, "run", "--rm", "--network", "none", "--entrypoint", entrypoint, IMAGE, *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout


def version(value: str) -> tuple[int, ...]:
    match = re.match(r"(?:go|v)?(\d+)\.(\d+)\.(\d+)", value)
    assert match is not None, f"unexpected version {value!r}"
    return tuple(int(part) for part in match.groups())


@pytest.mark.parametrize(
    ("tool", "dependencies"),
    [
        (
            "gospider",
            {
                "golang.org/x/crypto": "0.55.0",
                "golang.org/x/net": "0.60.0",
                "golang.org/x/text": "0.41.0",
                "github.com/antchfx/xmlquery": "1.3.1",
                "github.com/antchfx/xpath": "1.3.6",
                "github.com/sirupsen/logrus": "1.9.3",
            },
        ),
        ("httpx", {"github.com/klauspost/compress": "1.18.7", "golang.org/x/net": "0.60.0"}),
        (
            "interactsh-client",
            {"github.com/klauspost/compress": "1.18.7", "golang.org/x/net": "0.60.0"},
        ),
        (
            "katana",
            {
                "github.com/jackc/pgx/v5": "5.9.0",
                "golang.org/x/net": "0.60.0",
                "github.com/klauspost/compress": "1.18.7",
            },
        ),
        (
            "vulnx",
            {
                "github.com/klauspost/compress": "1.18.7",
                "golang.org/x/crypto": "0.55.0",
                "golang.org/x/net": "0.60.0",
                "golang.org/x/text": "0.41.0",
            },
        ),
        (
            "gitleaks",
            {
                "golang.org/x/crypto": "0.55.0",
                "golang.org/x/text": "0.41.0",
                "github.com/klauspost/compress": "1.18.7",
            },
        ),
        ("trivy", {"github.com/go-jose/go-jose/v4": "4.1.6"}),
    ],
)
@requires_image
def test_actual_binaries_embed_patched_dependencies(
    tool: str,
    dependencies: dict[str, str],
) -> None:
    output = image_command("go", "version", "-m", f"/home/pentester/go/bin/{tool}")
    assert version(output.splitlines()[0].split()[-1]) >= (1, 27, 3)
    installed = dict(re.findall(r"\bdep\s+(\S+)\s+(\S+)", output))
    for dependency, minimum in dependencies.items():
        assert version(installed[dependency]) >= version(minimum)
    argument = {
        "gospider": "-h",
        "gitleaks": "version",
        "trivy": "--version",
        "vulnx": "--help",
    }.get(tool, "-version")
    image_command(f"/home/pentester/go/bin/{tool}", argument)


@requires_image
def test_jshint_patched_dependencies_preserve_linting() -> None:
    image_command(
        "node",
        "-e",
        """
const assert = require('node:assert/strict');
const root = '/opt/strix-jshint/node_modules/';
assert.equal(require(root + 'lodash/package.json').version, '4.18.1');
assert.equal(require(root + 'minimatch/package.json').version, '3.1.5');
const match = require(root + 'minimatch');
assert(match('src/file.js', 'src/*.js'));
assert(!match('src/file.py', 'src/*.js'));
const lint = require(root + 'jshint').JSHINT;
assert(lint('var n = 1;'));
assert(!lint('var = ;'));
""",
    )


@requires_image
def test_dirsearch_crypto_works_and_rust_matches_are_source_only() -> None:
    image_command(
        "/home/pentester/.local/share/pipx/venvs/dirsearch/bin/python",
        "-c",
        """
import importlib.util
from importlib.metadata import distribution, version
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from OpenSSL import SSL
assert tuple(map(int, version('cryptography').split('.'))) >= (50, 0, 2)
cipher = AESGCM(AESGCM.generate_key(bit_length=128))
assert cipher.decrypt(b'0' * 12, cipher.encrypt(b'0' * 12, b'probe', None), None) == b'probe'
assert importlib.util.find_spec('dirsearch_native') is None
assert not list(distribution('dirsearch').locate_file('dirsearch').rglob('*.so'))
SSL.Context(SSL.TLS_CLIENT_METHOD)
""",
    )
    image_command("dirsearch", "--help")


def source_archive(requirement: str = "pyopenssl==26.1.0", name: str = "") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path, content in {
            "dirsearch-0.5.0/requirements/runtime.txt": requirement.encode(),
            name or "dirsearch-0.5.0/scanner.py": b"unchanged scanner",
        }.items():
            entry = tarfile.TarInfo(path)
            entry.size = len(content)
            archive.addfile(entry, io.BytesIO(content))
    return buffer.getvalue()


def test_dirsearch_source_digest_mismatch_fails_before_extraction(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="digest mismatch"):
        install_dirsearch.prepare_source(b"tampered", tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("mode", ["valid", "traversal", "unexpected-requirement"])
def test_dirsearch_source_patch_is_narrow_and_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    archive = source_archive(
        requirement="pyopenssl==0.0.0" if mode == "unexpected-requirement" else "pyopenssl==26.1.0",
        name="../outside.py" if mode == "traversal" else "",
    )
    monkeypatch.setattr(install_dirsearch, "SOURCE_SHA256", hashlib.sha256(archive).hexdigest())
    destination = tmp_path / "output"
    if mode == "traversal":
        with pytest.raises(tarfile.OutsideDestinationError):
            install_dirsearch.prepare_source(archive, destination)
        assert not (tmp_path / "outside.py").exists()
    elif mode == "unexpected-requirement":
        with pytest.raises(RuntimeError, match="Unexpected Dirsearch"):
            install_dirsearch.prepare_source(archive, destination)
    else:
        install_dirsearch.prepare_source(archive, destination)
        root = destination / "dirsearch-0.5.0"
        assert (root / "scanner.py").read_bytes() == b"unchanged scanner"
        assert (root / "requirements/runtime.txt").read_text() == (
            "pyopenssl==26.4.0\ncryptography==50.0.2"
        )
