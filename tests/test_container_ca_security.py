"""A distributed sandbox image must not distribute a shared CA private key."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]


def test_image_does_not_generate_or_install_a_shared_ca() -> None:
    dockerfile = (ROOT / "containers/Dockerfile").read_text(encoding="utf-8")
    assert "RUN openssl ecparam" not in dockerfile
    assert "RUN cp /app/certs/ca.crt" not in dockerfile
    assert "COPY containers/generate-ca.sh" in dockerfile
    entrypoint = (ROOT / "containers/docker-entrypoint.sh").read_text(encoding="utf-8")
    assert entrypoint.index("strix-generate-ca.sh") < entrypoint.index("caido-cli --listen")
    assert "sudo update-ca-certificates" in entrypoint


@pytest.mark.skipif(os.name == "nt", reason="POSIX container script; execute on Linux CI")
def test_containers_get_distinct_private_signing_keys(tmp_path: Path) -> None:
    shell = shutil.which("sh")
    if shell is None or shutil.which("openssl") is None:
        pytest.skip("shell and OpenSSL required")
    script = ROOT / "containers/generate-ca.sh"
    first, second = tmp_path / "one", tmp_path / "two"
    for directory in (first, second):
        subprocess.run([shell, str(script), str(directory)], check=True, capture_output=True)  # noqa: S603
        assert stat.S_IMODE((directory / "ca.key").stat().st_mode) == 0o600
        assert stat.S_IMODE((directory / "ca.p12").stat().st_mode) == 0o600
    assert (first / "ca.key").read_bytes() != (second / "ca.key").read_bytes()
    assert (first / "ca.crt").read_bytes() != (second / "ca.crt").read_bytes()
