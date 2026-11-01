"""Prepare unchanged Dirsearch source with a compatible patched TLS dependency pair."""

import hashlib
import io
import sys
import tarfile
import urllib.request
from pathlib import Path


SOURCE_SHA256 = "8295dcf154c9c42bf01c0e41a743d1677fb80ff424906f7de5c1ac05aaaa79ee"


def prepare_source(archive: bytes, destination: Path) -> None:
    if hashlib.sha256(archive).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("Dirsearch source digest mismatch")
    destination.mkdir(mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(destination, filter="data")
    requirements = destination / "dirsearch-0.5.0/requirements/runtime.txt"
    text = requirements.read_text(encoding="utf-8")
    if text.count("pyopenssl==26.1.0") != 1:
        raise RuntimeError("Unexpected Dirsearch TLS requirements")
    requirements.write_text(
        text.replace("pyopenssl==26.1.0", "pyopenssl==26.4.0\ncryptography==50.0.2"),
        encoding="utf-8",
    )


if __name__ == "__main__":
    with urllib.request.urlopen(
        "https://files.pythonhosted.org/packages/12/45/aa4aad4b6f7fe7d337d9656ce57412e37ff696f52a05739ed10c5ffa6adf/dirsearch-0.5.0.tar.gz",
        timeout=120,
    ) as response:
        prepare_source(response.read(), Path(sys.argv[1]))
