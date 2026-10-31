"""Transport HTTP : succes, 204 et mapping d'erreurs API."""

import httpx
import pytest
import respx

from gandal_sdk._http import HttpTransport
from gandal_sdk.errors import GandalApiError


@respx.mock
def test_request_returns_json_on_success() -> None:
    """Un 200 JSON est renvoye tel quel."""
    respx.get("http://example.test/api/v1/health").respond(200, json={"status": "ok"})
    transport = HttpTransport("http://example.test")
    try:
        assert transport.request("GET", "/api/v1/health") == {"status": "ok"}
    finally:
        transport.close()


@respx.mock
def test_request_returns_none_on_204() -> None:
    """Un 204 sans corps donne None."""
    respx.delete("http://example.test/api/v1/x").respond(204)
    transport = HttpTransport("http://example.test")
    try:
        assert transport.request("DELETE", "/api/v1/x") is None
    finally:
        transport.close()


@respx.mock
def test_request_maps_api_error_envelope() -> None:
    """Le format {error: {...}} devient GandalApiError."""
    respx.get("http://example.test/api/v1/x").respond(
        404,
        json={"error": {"code": "not_found", "message": "absent", "details": None}},
    )
    transport = HttpTransport("http://example.test")
    try:
        with pytest.raises(GandalApiError) as caught:
            transport.request("GET", "/api/v1/x")
        assert caught.value.code == "not_found"
        assert caught.value.status == 404
    finally:
        transport.close()


@respx.mock
def test_request_sends_bearer_when_set() -> None:
    """Le jeton est injecte dans Authorization."""
    route = respx.get("http://example.test/api/v1/auth/me").respond(
        200, json={"user_id": "u1", "email": "a@b.c", "first_name": "A", "last_name": "B", "role": "user"}
    )
    transport = HttpTransport("http://example.test")
    transport.set_token("tok-123")
    try:
        transport.request("GET", "/api/v1/auth/me")
        assert route.calls[0].request.headers["Authorization"] == "Bearer tok-123"
    finally:
        transport.close()


@respx.mock
def test_request_raises_on_non_json_error() -> None:
    """Une erreur non JSON reste une GandalApiError."""
    respx.get("http://example.test/boom").respond(500, text="down")
    transport = HttpTransport("http://example.test")
    try:
        with pytest.raises(GandalApiError) as caught:
            transport.request("GET", "/boom")
        assert caught.value.status == 500
    finally:
        transport.close()


def test_close_is_safe_with_injected_client() -> None:
    """close() ne ferme pas un client httpx injecte."""
    client = httpx.Client(base_url="http://example.test")
    transport = HttpTransport("http://example.test", client=client)
    transport.close()
    # le client injecte reste utilisable
    client.close()
