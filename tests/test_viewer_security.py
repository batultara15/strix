"""Regression coverage for the viewer HTTP trust boundary."""

from __future__ import annotations

import http.client
import threading
from http.server import ThreadingHTTPServer
from typing import TYPE_CHECKING

import pytest

from strix.interface.viewer.server import _make_handler, _ViewerState


if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def viewer(tmp_path: Path) -> Iterator[ThreadingHTTPServer]:
    state = _ViewerState(tmp_path / "run", tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("headers", "status"),
    [
        ([("Content-Length", "-1")], 400),
        ([("Content-Length", "invalid")], 400),
        ([("Content-Length", "65537")], 413),
        ([("Content-Length", "9" * 100)], 413),
        ([("Content-Length", "2"), ("Content-Length", "2")], 400),
        ([("Transfer-Encoding", "chunked")], 400),
    ],
)
def test_rejects_bad_framing_without_waiting_for_body(
    viewer: ThreadingHTTPServer, headers: list[tuple[str, str]], status: int
) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", viewer.server_port, timeout=2)
    try:
        connection.putrequest("POST", "/api/event")
        for name, value in headers:
            connection.putheader(name, value)
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == status
        response.read()
    finally:
        connection.close()


def test_small_valid_request_still_works(viewer: ThreadingHTTPServer) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", viewer.server_port, timeout=2)
    try:
        connection.request("POST", "/api/event", b"{}", {"Content-Type": "application/json"})
        response = connection.getresponse()
        assert response.status == 204
        response.read()
    finally:
        connection.close()


def test_bootstrap_capability_never_reaches_access_logs(
    viewer: ThreadingHTTPServer, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG", logger="strix.interface.viewer.server")
    connection = http.client.HTTPConnection("127.0.0.1", viewer.server_port, timeout=2)
    try:
        connection.request("GET", "/?token=TEST_FAKE_VIEWER_CAPABILITY&email=FAKE_PRIVATE")
        response = connection.getresponse()
        response.read()
        assert response.getheader("Cache-Control") == "no-store"
        assert response.getheader("Referrer-Policy") == "no-referrer"
        assert response.getheader("X-Content-Type-Options") == "nosniff"
        assert response.getheader("X-Frame-Options") == "DENY"
        assert "TEST_FAKE_VIEWER_CAPABILITY" not in caplog.text
        assert "FAKE_PRIVATE" not in caplog.text
        assert "GET / HTTP/1.1" in caplog.text
    finally:
        connection.close()
