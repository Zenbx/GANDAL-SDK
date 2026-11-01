"""Relances sur de vraies sockets : serveur HTTP local, attentes reelles, port ferme."""

from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from gandal_sdk import GandalApiError, GandalClient, RetryPolicy


class _ScriptedHandler(BaseHTTPRequestHandler):
    """Repond selon la file de reponses du serveur, une par requete recue."""

    def _reply(self) -> None:
        server = self.server
        server.hits.append(self.command)  # type: ignore[attr-defined]
        status, headers, body = server.script.pop(0)  # type: ignore[attr-defined]
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = _reply

    def log_message(self, *args: object) -> None:
        """Silence : pas de journal d'acces dans la sortie des tests."""


@pytest.fixture
def server() -> Iterator[ThreadingHTTPServer]:
    """Serveur HTTP reel sur un port libre de 127.0.0.1."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _ScriptedHandler)
    httpd.script = []  # type: ignore[attr-defined]
    httpd.hits = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=httpd.serve_forever, args=(0.05,), daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def _url(httpd: ThreadingHTTPServer) -> str:
    host, port = httpd.server_address[:2]
    return f"http://{host}:{port}"


UNAVAILABLE = {"error": {"code": "upstream_unavailable", "message": "panne", "details": None}}


def test_retry_after_is_really_waited(server: ThreadingHTTPServer) -> None:
    """429 avec Retry-After: 1 : la deuxieme requete part au moins 1 s plus tard."""
    server.script += [(429, {"Retry-After": "1"}, {"detail": "trop vite"}), (200, {}, {"ok": 1})]
    with GandalClient(_url(server)) as client:
        started = time.monotonic()
        assert client._http.request("GET", "/x") == {"ok": 1}
        assert time.monotonic() - started >= 1.0
    assert server.hits == ["GET", "GET"]


def test_post_not_replayed_on_503(server: ThreadingHTTPServer) -> None:
    """Le serveur ne recoit qu'un seul POST : pas de doublon possible."""
    server.script += [(503, {}, UNAVAILABLE), (201, {}, {"id": 1})]
    with GandalClient(_url(server)) as client:
        with pytest.raises(GandalApiError) as caught:
            client._http.request("POST", "/x", json={})
    assert caught.value.code == "upstream_unavailable"
    assert server.hits == ["POST"]


def test_get_503_replayed_until_success(server: ThreadingHTTPServer) -> None:
    """Deux 503 puis 200 : trois requetes reelles."""
    server.script += [(503, {}, UNAVAILABLE), (503, {}, UNAVAILABLE), (200, {}, {"ok": 1})]
    policy = RetryPolicy(base_delay=0.01)
    with GandalClient(_url(server), retry=policy) as client:
        assert client._http.request("GET", "/x") == {"ok": 1}
    assert len(server.hits) == 3


def test_connection_refused_is_retried_then_raised() -> None:
    """Port ferme : vraie erreur de connexion, rejouee en GET puis remontee."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    # Le port vient d'etre libere : personne n'ecoute dessus.
    policy = RetryPolicy(max_attempts=3, base_delay=0.01)
    with GandalClient(f"http://127.0.0.1:{port}", retry=policy) as client:
        started = time.monotonic()
        with pytest.raises(httpx.ConnectError):
            client._http.request("GET", "/x")
        assert time.monotonic() - started < 5
